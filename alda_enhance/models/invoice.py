# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api,exceptions
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp
from logging import getLogger

_logger = getLogger(__name__)

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'


    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity == 0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
            price_discount  = (line.price_subtotal/self.before_discount)*self.fixed_discount if self.before_discount else 0

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal - price_discount,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
                'analytic_tag_ids': analytic_tag_ids
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        return res

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        res['bonus'] = line.bonus
        return res


class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    bonus = fields.Float(
        string='Bonus',
        default=0.0,
        digits=dp.get_precision('Product Unit of Measure'),
    )

    @api.one
    def compute_totals(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        d1 = self.discount / 100.0
        d2 = self.discount2 / 100.0
        price = self.price_unit * (1 - d1 - d2 + d1 * d2) - self.fixed_discount / self.quantity if self.quantity else 0
        total = {
            'total_excluded':self.quantity * price,
            'total_included':self.quantity * price,
            'total_tax':0.0,
        }
        if self.invoice_line_tax_ids:
            total = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
            total['total_tax'] = total['total_included'] - total['total_excluded']
        return total

    # @api.one
    # @api.constrains ('product_id', 'purchase_id')
    # def prevent_vendor_bill(self):
    #     if self.product_id.type == 'product' and not self.purchase_id and self.invoice_id.type == 'in_invoice':
    #         raise exceptions.ValidationError(_("You cannot create an invoice for stockable product without purchase order"))







