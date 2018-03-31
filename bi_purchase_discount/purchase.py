# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 BrowseInfo(<http://www.browseinfo.in>).
#    $autor:
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }


    fixed_discount = fields.Float('Discount', digits=dp.get_precision('Discount'),states=READONLY_STATES)
    total_before_fixed_discount = fields.Float('Before Discount', digits=dp.get_precision('Discount'),compute='_amount_all', track_visibility='always')

    @api.depends('order_line.price_total','fixed_discount')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax =  total_before_fixed_discount = 0.0
            for line in order.order_line:
                total_before_fixed_discount += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            amount_untaxed  = total_before_fixed_discount - order.fixed_discount
            order.update({
                'total_before_fixed_discount':order.currency_id.round(total_before_fixed_discount),
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount 1 (%)',digits=dp.get_precision('Discount'))
    discount2 = fields.Float('Discount 2 (%)',digits=dp.get_precision('Discount'))
    fixed_discount = fields.Float('Discount',digits=dp.get_precision('Discount'))

    @api.depends('product_qty', 'price_unit', 'taxes_id','discount','discount2','fixed_discount')
    def _compute_amount(self):
        for line in self:
            d1 = line.discount / 100.0
            d2 = line.discount2 / 100.0
            price_unit = line.price_unit * (1 - d1 - d2 + d1 * d2) - line.fixed_discount
            taxes = line.taxes_id.compute_all(price_unit, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'] ,
                'price_subtotal': taxes['total_excluded'],
            })


   
        


