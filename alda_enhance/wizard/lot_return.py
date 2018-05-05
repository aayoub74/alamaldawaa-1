from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round,float_compare

from logging import getLogger

_logger = getLogger(__name__)

class ReturnQuantLine(models.TransientModel):
    _name = 'stock.return.quant.line'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'), required=True)
    wizard_id = fields.Many2one('stock.return.quant', string="Wizard")
    quant_id = fields.Many2one('stock.quant','Quant')
    warehouse_id = fields.Many2one('stock.warehouse',compute='_get_warehouse')
    location_id = fields.Many2one('stock.location',string="Location")
    orig_qty = fields.Float(
        'Original Qty', 
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_qty_bouns',
        )
    bouns = fields.Float(
        'Bouns', 
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_qty_bouns',
        )

    @api.depends('quantity')
    def _get_qty_bouns(self):
        for line in self:
            if line.quantity:
                line.bouns = float_round(value=line.quantity*line.wizard_id.b_ratio,
                    precision_digits=0)
                line.orig_qty = line.quantity - line.bouns

    @api.depends('quant_id')
    def _get_warehouse(self):
        for line in self:
            line['warehouse_id'] = line.quant_id.location_id.get_warehouse()

class ReturnQuant(models.TransientModel):
    _name = 'stock.return.quant'
    _description = 'Return Quant'

    product_return_moves = fields.One2many('stock.return.quant.line', 'wizard_id', 'Quants')
    lot_id = fields.Many2one('stock.production.lot', "Lot")
    location_id = fields.Many2one(
        'stock.location', 'Return Location',
        domain="[('usage', '=', 'supplier')]",required=True)
    b_ratio = fields.Float('Bouns Ratio',digits=(16,3),default=0.0)

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError("You may only return one Lot at a time!")
        res = super(ReturnQuant, self).default_get(fields)

        lot_obj = self.env['stock.production.lot']
        move_dest_exists = False
        product_return_moves = []
        lot = lot_obj.browse(self.env.context.get('active_id'))
        if lot:
            for quant in lot.quant_ids.filtered(lambda qu:qu.location_id.usage in ['internal','transit'] and not qu.reservation_id):
                product_return_moves.append((0, 0, {'product_id': quant.product_id.id, 'quantity': 0.0, 'quant_id':quant.id,'location_id':quant.location_id.id}))
            if not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'lot_id' in fields:
                res.update({'lot_id':lot.id})
            if 'b_ratio' in fields:
                res.update({'b_ratio':lot.b_ratio})
        return res
        
    @api.multi
    def _create_returns(self):

        #Group by warehouse
        self.ensure_one()
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        warehouses = self.product_return_moves.mapped('warehouse_id')
        res = []


        for warehouse in warehouses:
            return_moves = self.product_return_moves.filtered(lambda rm:rm.warehouse_id == warehouse)
            picking_type = warehouse.out_type_id

            new_picking = {
                'move_lines': [],
                'picking_type_id': picking_type.id,
                'state': 'draft',
                'origin': "Retrun of lot "+self.lot_id.name,
                'location_dest_id': self.location_id.id,
                'location_id': picking_type.default_location_src_id.id,
             
                }

            picking = picking_obj.create(new_picking)
            picking.message_post_with_view('mail.message_origin_link',
                values={'self': picking, 'origin': self.lot_id},
                subtype_id=self.env.ref('mail.mt_note').id)
            
            returned_lines = 0 
            for return_line in return_moves:
                qty = return_line.quantity

                if qty:
                    returned_lines += 1
                    move_line = {
                        'product_id': return_line.product_id.id,
                        'product_uom_qty': qty,
                        'picking_id': picking.id,
                        'state': 'draft',
                        'location_id': return_line.quant_id.location_id.id,
                        'location_dest_id': self.location_id.id,
                        'picking_type_id': picking_type.id,
                        'warehouse_id': warehouse.id,
                        'procure_method': 'make_to_stock',
                        'product_uom': return_line.quant_id.product_uom_id.id,
                        'name' : "Retrun of lot " + self.lot_id.name,
                    }
                    move = move_obj.create(move_line)
                    #create  "stock.pack.operation" and link it to picking
                    op_vals = {
                        'picking_id':picking.id,
                        'product_id':return_line.product_id.id,
                        'product_uom_id':return_line.quant_id.product_uom_id.id,
                        'product_qty':qty,
                        'ordered_qty':qty,
                        'location_id':return_line.quant_id.location_id.id,
                        'location_dest_id':self.location_id.id,
                        'orig_qty':return_line.orig_qty,
                        'bouns':return_line.bouns,
                    }
                    #print op_vals
                    #import pdb;pdb.set_trace()
                    ctx_op = dict(self.env.context)
                    ctx_op.update({'stop':True})
                    operation = self.env['stock.pack.operation'].with_context(ctx_op).create(op_vals)

                    #create stock.pack.operation.lot and with lot id and link it to operation
                    op_lot_vals={
                        'operation_id':operation.id,
                        'lot_id':self.lot_id.id,
                        'qty':qty,
                        'qty_todo':qty,
                    }
                    op_lot = self.env['stock.pack.operation.lot'].create(op_lot_vals)
                    #create stock.move.operation.link and link it to move and operation and quant
                    smol_vals = {
                        'qty':qty,
                        'operation_id':operation.id,
                        'move_id':move.id,
                        'reserved_quant_id':return_line.quant_id.id,
                    }
                    smol = self.env['stock.move.operation.link'].create(smol_vals)
                    

            if not returned_lines:
                raise UserError(_("Please specify at least one non-zero quantity."))

            picking.action_confirm()
            #import pdb; pdb.set_trace()
            ctx = dict(self.env.context)
            ctx.update({'reserve_only_ops':True,'no_prepare':True})
            picking.with_context(ctx).action_assign()
            res.append((picking.id, picking_type.id))
        return res

    @api.multi
    def create_returns(self):
        for wizard in self:
            res = wizard._create_returns()
        # Override the context to disable all the potential filters that could have been set previously
        domain = [('id','in',[resid[0] for resid in res])]
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_picking_type_id': False,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        return {
            'name': _('Returned Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form,calendar',
            'res_model': 'stock.picking',
            'domain': domain,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }