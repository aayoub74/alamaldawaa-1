from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round,float_compare
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.stock.models.stock_production_lot import ProductionLot
import datetime

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_prepare_partial(self):
        # TDE CLEANME: oh dear ...
        PackOperation = self.env['stock.pack.operation']

        # get list of existing operations and delete them
        existing_packages = PackOperation.search([('picking_id', 'in', self.ids)])  # TDE FIXME: o2m / m2o ?
        if existing_packages:
            existing_packages.unlink()
        for picking in self:
            forced_qties = {}  # Quantity remaining after calculating reserved quants
            picking_quants = self.env['stock.quant']
            # Calculate packages, reserved quants, qtys of this picking's moves
            for move in picking.move_lines:
                if move.state not in ('assigned', 'confirmed', 'waiting'):
                    continue
                move_quants = move.reserved_quant_ids
                picking_quants += move_quants
                forced_qty = 0.0
                if move.state == 'assigned':
                    qty = move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id, round=False)
                    forced_qty = qty - sum([x.qty for x in move_quants])
                # if we used force_assign() on the move, or if the move is incoming, forced_qty > 0
                if float_compare(forced_qty, 0, precision_rounding=move.product_id.uom_id.rounding) > 0:
                    if forced_qties.get(move.product_id):
                        forced_qties[move.product_id] += forced_qty
                    else:
                        forced_qties[move.product_id] = forced_qty
            for vals in picking._prepare_pack_ops(picking_quants, forced_qties):
                vals['fresh_record'] = False
                PackOperation |= PackOperation.create(vals)
        # recompute the remaining quantities all at once
        self.do_recompute_remaining_quantities()
        for pack in PackOperation:
            pack.ordered_qty = sum(
                pack.mapped('linked_move_operation_ids').mapped('move_id').filtered(lambda r: r.state != 'cancel').mapped('ordered_qty')
            )
            #added by eslam
            ctx = dict(self.env.context)
            ctx.update({'compute_qty':True})
            pack.with_context(ctx).bouns = sum(
                pack.mapped('linked_move_operation_ids').mapped('move_id').filtered(lambda r: r.state != 'cancel').mapped('bouns')
                )
             
        self.write({'recompute_pack_op': False})

    def _create_lots_for_picking(self):
        Lot = self.env['stock.production.lot']
        for pack_op_lot in self.mapped('pack_operation_ids').mapped('pack_lot_ids'):
            if not pack_op_lot.lot_id:
                b_ratio = float(pack_op_lot.operation_id.bouns)/float(pack_op_lot.operation_id.qty_done)
                lot = Lot.create({'name': pack_op_lot.lot_name, 'product_id': pack_op_lot.operation_id.product_id.id,'life_date':pack_op_lot.life_date,'b_ratio':b_ratio})
                pack_op_lot.write({'lot_id': lot.id})
        # TDE FIXME: this should not be done here
        self.mapped('pack_operation_ids').mapped('pack_lot_ids').filtered(lambda op_lot: op_lot.qty == 0.0).unlink()

    @api.multi
    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """
        no_prepare = self.env.context.get('no_prepare',False)
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        moves.action_assign(no_prepare=no_prepare)
        return True



class StockQuant(models.Model):
    _inherit = 'stock.quant'

    removal_date = fields.Date(related='lot_id.removal_date', store=True)
    life_date = fields.Date(related='lot_id.life_date', store=True)
    expiry_state = fields.Selection(
        selection=[('expired', 'Expired'),
                   ('alert', 'In alert'),
                   ('normal', 'Normal'),
                   ('to_remove', 'To remove'),
                   ('best_before', 'After the best before')],
        string="Expiry State",
        related="lot_id.expiry_state",
        store=True)

class StockPackOperationLot(models.Model):
    """ Adding Production Date"""

    _inherit = 'stock.pack.operation.lot'
    
    life_date = fields.Date(
        string='Expiry Date',
        default=lambda self :fields.Date.today(),
    )

class StockProductionLotInherit1(models.Model):
    _inherit = 'stock.production.lot'

    @api.one
    @api.constrains('removal_date', 'alert_date', 'life_date', 'use_date')
    def _check_dates(self):
        dates = filter(lambda x: x, [self.alert_date, self.removal_date,self.life_date])
        sort_dates = list(dates)
        sort_dates.sort()
        if dates != sort_dates:
            raise UserError(
                _('Dates must be: Alert Date < Removal Date < Expiry Date'))

   

    def _get_dates(self, product_id=None,life_date=None):
        """Returns dates based on number of days configured in current lot's product."""
        mapped_fields = {
            #'life_date': 'life_time',
            'use_date': 'use_time',
            'removal_date': 'removal_time',
            'alert_date': 'alert_time'
        }
        res = dict.fromkeys(mapped_fields.keys(), False)
        product = self.env['product.product'].browse(product_id) or self.product_id
        if product:
            for field in mapped_fields.keys():
                duration = getattr(product, mapped_fields[field])
                if duration:
                    ldate = life_date or self.life_date
                    date = datetime.datetime.strptime(ldate,DEFAULT_SERVER_DATE_FORMAT) - datetime.timedelta(days=duration)
                    res[field] = fields.Date.to_string(date)
        return res

    @api.one
    @api.depends('removal_date', 'alert_date', 'life_date', 'use_date')
    def _get_product_state(self):
        now = fields.Date.today()
        self.expiry_state = 'normal'
        if self.life_date and self.life_date < now:
            self.expiry_state = 'expired'
        elif (self.alert_date and self.removal_date and
                self.removal_date >= now > self.alert_date):
            self.expiry_state = 'alert'
        elif (self.removal_date and self.life_date and
                self.life_date >= now > self.removal_date):
            self.expiry_state = 'to_remove'

    expiry_state = fields.Selection(
        compute=_get_product_state,
        selection=[('expired', 'Expired'),
                   ('alert', 'In alert'),
                   ('normal', 'Normal'),
                   ('to_remove', 'To remove'),
                   ('best_before', 'After the best before')],
        string='Expiry state',store=True)


    life_date = fields.Date(string='Expiry Date',
        help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.')
    use_date = fields.Date(string='Best before Date',
        help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
    removal_date = fields.Date(string='Removal Date',
        help='This is the date on which the goods with this Serial Number should be removed from the stock.')
    alert_date = fields.Date(string='Alert Date',
        help="This is the date on which an alert should be notified about the goods with this Serial Number.")

    b_ratio = fields.Float('Bouns Ratio',digits=(16,3),default=0.0)

    @api.model
    def create(self, vals):
        dates = self._get_dates(vals.get('product_id'),vals.get('life_date'))
        for d in dates.keys():
            if not vals.get(d):
                vals[d] = dates[d]
        return super(ProductionLot, self).create(vals)

    @api.onchange('life_date')
    def change_dates_pro(self):
        dates_dict = self._get_dates()
        for field, value in dates_dict.items():
            setattr(self, field, value)

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    bouns = fields.Float('Bouns', 
        digits=dp.get_precision('Product Unit of Measure'),default=0.0)

class StockPackOperation(models.Model):
    ''' Adding Bouns Ratio to stock Pack Operation '''
    _inherit = 'stock.pack.operation'


    orig_qty = fields.Float(
        'Original Qty', 
        digits=dp.get_precision('Product Unit of Measure'))
    bouns = fields.Float(
        'Bouns', 
        digits=dp.get_precision('Product Unit of Measure'))

    @api.onchange('bouns')
    def _set_orig_qty(self):
        #import pdb;pdb.set_trace()
        #print 'bouns',self.bouns,self.qty_done,self.product_qty
        if self.bouns <= self.qty_done:
            self.orig_qty = self.qty_done - self.bouns
        elif self.bouns <= self.product_qty:
            self.orig_qty = self.product_qty - self.bouns


    @api.onchange('orig_qty')
    def _set_bouns_qty(self):
        #import pdb;pdb.set_trace()
        #print 'orig_qty',self.orig_qty,self.qty_done,self.product_qty
        if self.orig_qty <= self.qty_done:
            self.bouns = self.qty_done - self.orig_qty
        elif self.orig_qty <= self.product_qty:
            self.bouns = self.product_qty - self.orig_qty


    @api.multi
    def write(self,vals):
        #import pdb;pdb.set_trace()
        if self.env.context.get('compute_qty',False):
            self.ensure_one()
            if self.qty_done:
                vals['orig_qty'] = self.qty_done - vals['bouns']
            else:
                vals['orig_qty'] = self.product_qty - vals['bouns']
        res = super(StockPackOperation, self).write(vals)
        if vals.get('qty_done',False) :
            ctx = dict(self.env.context)
            ctx.update({'compute_qty':False})
            for rec in self:
                ratio = rec.bouns / rec.product_qty
                bouns = float_round(value=rec.qty_done*ratio,
                     precision_digits=0)
                orig_qty = rec.qty_done - bouns
                rec.with_context(ctx).write(
                    {
                    'bouns':bouns,
                    'orig_qty':orig_qty,
                    })
        return res



           
    # @api.depends('b_ratio','product_qty','qty_done')
    # def _get_qty_bouns(self):
    #     for pack in self:
    #         if pack.qty_done:
    #             pack.bouns = float_round(value=pack.qty_done*pack.b_ratio,
    #                 precision_digits=0)
    #             pack.orig_qty = pack.qty_done - pack.bouns
    #         else:
    #             pack.bouns = float_round(value=pack.product_qty*pack.b_ratio,
    #                 precision_digits=0)
    #             pack.orig_qty = pack.product_qty - pack.bouns

                
