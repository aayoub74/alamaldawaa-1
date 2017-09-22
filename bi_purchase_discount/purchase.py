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
from odoo.tools.float_utils import float_is_zero, float_compare

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount %')


    @api.depends('product_qty', 'price_unit', 'taxes_id','discount')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            if line.discount:
                discount = (line.price_unit * line.discount * line.product_qty)/100
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'] ,
                    'price_subtotal': taxes['total_excluded'] - discount,
                })
            else:
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })


   
        


