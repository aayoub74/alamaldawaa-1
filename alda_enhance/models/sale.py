from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare,DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    READONLY_STATES= {
        'sale':[('readonly', True)],
        'done':[('readonly', True)],
        'cancel':[('readonly', True)],
    }

    fixed_discount = fields.Float('Discount', digits=dp.get_precision('Discount'), states=READONLY_STATES)
    total_before_fixed_discount = fields.Float('Before Discount', digits=dp.get_precision('Discount'),
                                               compute='_amount_all', track_visibility='always')
    type_invoice_policy = fields.Selection(
        selection=[('normal', 'By Product'),
                   ('prepaid', 'Before Delivery')],
        related='warehouse_id.type_invoice_policy',readonly=True
    )

    is_paid = fields.Boolean(string="Is paid?",compute='_check_payment')

    @api.depends('order_line.invoice_lines.invoice_id.state','order_line.product_uom_qty','order_line.qty_invoiced')
    def _check_payment(self):
        for rec in self:
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            invoice_status = rec.mapped('order_line.invoice_lines.invoice_id.state')
            rec.is_paid = False if (set(invoice_status) - set(['paid'])) or any(
                float_compare(
                    line.product_uom_qty, line.qty_invoiced,
                    precision_digits=precision) > 0
            for line in rec.order_line) else True

    @api.depends('order_line.price_total','fixed_discount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = total_before_fixed_discount =0.0
            for line in order.order_line:
                total_before_fixed_discount += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    d1 = line.discount / 100.0
                    d2 = line.discount2 / 100.0
                    discount = (line.price_unit) * (d1 + d2 - d1 * d2)

                    price = line.price_unit - discount
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            amount_untaxed = total_before_fixed_discount - order.fixed_discount
            order.update({
                'total_before_fixed_discount': order.pricelist_id.currency_id.round(total_before_fixed_discount),
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        res['fixed_discount'] = self.fixed_discount
        return res



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    total_qty = fields.Float(
        string='Total Qty',
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_total',

    )
    bonus = fields.Float(string='Bonus', digits=dp.get_precision('Product Unit of Measure'))
    discount2 = fields.Float('Discount 2 (%)', digits=dp.get_precision('Discount'))
    fixed_discount = fields.Float('Discount', digits=dp.get_precision('Discount'))


    # @api.onchange('product_id')
    # def get_discount(self):
    #     self.discount2 = self.product_id.sale_discount


    @api.depends('bonus', 'product_uom_qty')
    def _compute_total(self):
        ''' Calcualte Total Qty and bouns ratio from Total Qty '''
        for record in self:
            record.total_qty = record.bonus + record.product_uom_qty

    @api.depends('product_uom_qty', 'discount', 'discount2', 'price_unit', 'tax_id','fixed_discount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            d1 = line.discount / 100.0
            d2 = line.discount2 / 100.0
            discount = (line.price_unit) * (d1 + d2 - d1 * d2)

            price = line.price_unit - discount
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'] - line.fixed_discount,
            })

    @api.depends('price_unit', 'discount', 'discount2')
    def _get_price_reduce(self):
        for line in self:
            d1 = line.discount / 100.0
            d2 = line.discount2 / 100.0
            discount = (line.price_unit) * (d1 + d2 - d1 * d2)
            line.price_reduce = line.price_unit - discount - line.fixed_discount

    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        currency = self.currency_id or self.company_id.currency_id
        for line in self.order_line:
            base_tax = 0
            for tax in line.tax_id:
                group = tax.tax_group_id
                res.setdefault(group, 0.0)
                # FORWARD-PORT UP TO SAAS-17
                d1 = line.discount / 100.0
                d2 = line.discount2 / 100.0
                discount = (line.price_unit) * (d1 + d2 - d1 * d2)
                price_reduce = line.price_unit - discount - line.fixed_discount
                taxes = tax.compute_all(price_reduce + base_tax, quantity=line.product_uom_qty,
                                        product=line.product_id, partner=self.partner_shipping_id)['taxes']
                for t in taxes:
                    res[group] += t['amount']
                if tax.include_base_amount:
                    base_tax += tax.compute_all(price_reduce + base_tax, quantity=1, product=line.product_id,
                                                partner=self.partner_shipping_id)['taxes'][0]['amount']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = map(lambda l: (l[0].name, l[1]), res)
        return res

    @api.multi
    def _action_procurement_create(self):
        """
        Create procurements based on quantity ordered. If the quantity is increased, new
        procurements are created. If the quantity is decreased, no automated action is taken.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order']  # Empty recordset
        for line in self:
            if line.state != 'sale' or not line.product_id._need_procurement():
                continue
            qty = 0.0
            for proc in line.procurement_ids:
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)

            vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)
            vals['product_qty'] = line.total_qty - qty
            new_proc = self.env["procurement.order"].with_context(procurement_autorun_defer=True).create(vals)
            new_proc.message_post_with_view('mail.message_origin_link',
                values={'self': new_proc, 'origin': line.order_id},
                subtype_id=self.env.ref('mail.mt_note').id)
            new_procs += new_proc
        new_procs.run()
        return new_procs

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res  = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res['discount2'] = self.discount2
        res['fixed_discount'] = self.fixed_discount
        return  res


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _get_stock_move_values(self):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        group_id = False
        if self.rule_id.group_propagation_option == 'propagate':
            group_id = self.group_id.id
        elif self.rule_id.group_propagation_option == 'fixed':
            group_id = self.rule_id.group_id.id
        date_expected = (datetime.strptime(self.date_planned, DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(days=self.rule_id.delay or 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_done = sum(self.move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
        qty_left = max(self.product_qty - qty_done, 0)
        bonus = 0.0
        if self.sale_line_id:
            bonus = self.sale_line_id.bonus
        return {
            'name': self.name,
            'company_id': self.rule_id.company_id.id or self.rule_id.location_src_id.company_id.id or self.rule_id.location_id.company_id.id or self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.rule_id.partner_address_id.id or (self.group_id and self.group_id.partner_id.id) or False,
            'location_id': self.rule_id.location_src_id.id,
            'location_dest_id': self.location_id.id,
            'move_dest_id': self.move_dest_id and self.move_dest_id.id or False,
            'procurement_id': self.id,
            'rule_id': self.rule_id.id,
            'procure_method': self.rule_id.procure_method,
            'origin': self.origin,
            'picking_type_id': self.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in self.route_ids],
            'warehouse_id': self.rule_id.propagate_warehouse_id.id or self.rule_id.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.rule_id.propagate,
            'priority': self.priority,
            'bouns': bonus,
        }
