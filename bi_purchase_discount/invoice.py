from odoo import models, fields, api
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    discount = fields.Float(string='Discount 1 (%)', digits=dp.get_precision('Discount'),default=0.0)
    discount2 = fields.Float(string='Discount 2 (%)', digits=dp.get_precision('Discount'),default=0.0)
    fixed_discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'),default=0.0)

    @api.one
    @api.depends('price_unit', 'discount', 'discount2', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice','fixed_discount')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        d1 = self.discount / 100.0
        d2 = self.discount2 / 100.0
        price = self.price_unit * (1 - d1-d2+d1*d2) - self.fixed_discount/self.quantity if self.quantity else 0
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id.date_invoice).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'
    fixed_discount = fields.Float(string="Discount", digits=dp.get_precision('Discount'), default=0.0)
    before_discount = fields.Float(string="Subtotal before Discount", digits=dp.get_precision('Discount'), default=0.0,compute='_compute_amount')



    @api.onchange('fixed_discount')
    def _onchange_fixed_discount(self):
        return self._onchange_invoice_line_ids()

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
                 'type','fixed_discount')
    def _compute_amount(self):
        self.before_discount = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_untaxed = self.before_discount - self.fixed_discount
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            d1 = line.discount / 100.0
            d2 = line.discount2 / 100.0
            price_unit = line.price_unit * (1 - d1-d2+d1*d2) - (line.fixed_discount/line.quantity if line.quantity else 1)
            price_unit -= (self.fixed_discount /self.before_discount) * price_unit
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id
        self.fixed_discount = self.purchase_id.fixed_discount

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.purchase_id = False
        return {}

    def _prepare_invoice_line_from_po_line(self, line):

        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        res['discount'] = line.discount
        res['discount2'] = line.discount2
        res['fixed_discount'] = line.fixed_discount
        return res
