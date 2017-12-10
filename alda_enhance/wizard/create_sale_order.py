# -*- coding: utf-8 -*-
from odoo import models,fields,api
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp

class QuotationWizard(models.TransientModel):
    _name = 'quotation.wizard'

    @api.model
    def _get_lines(self):
        res = []
        products = self.env['product.template'].browse(self._context.get('active_ids', []))
        for pro in products:
            line_data = {
                'product_id': pro.id,
                'qty':1.0,
                'bonus':0.0,
            }
            res.append((0, 0, line_data))
        return res

    partner_id = fields.Many2one('res.partner',string='Customer',domain=[('customer','=',True)],required=True)
    line_ids = fields.One2many('quotation.wizard.line','wizard_id',string='Lines',default=_get_lines)

    @api.returns('sale.order')
    def create_sale_order(self):
        self.ensure_one()
        sale_lines = []
        for line in self.line_ids:
            line_data = {
                'product_id':line.product_id.product_variant_id.id,
                'product_uom_qty':line.qty,
                'bonus':line.bonus,
                'discount':line.product_id.sale_discount,
                'discount2':line.product_id.sale_discount2,
            }
            sale_lines.append((0,0,line_data))
        sale_vals = {
            'partner_id':self.partner_id.id,
            'order_line':sale_lines,
        }
        return self.env['sale.order'].create(sale_vals)

    @api.multi
    def create_view_sale_order(self):
        self.ensure_one()
        sale_order_rec = self.create_sale_order()
        return {
            'name': _('Sale order'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': "{'search_default_name': '%s'}" % (sale_order_rec.name)
        }



class QuotationWizardLine(models.TransientModel):
    _name = 'quotation.wizard.line'

    wizard_id = fields.Many2one('quotation.wizard',string='Wizard')
    product_id = fields.Many2one('product.template',string="Product",required=True)
    qty = fields.Float('Qty',digits=dp.get_precision('Product Unit of Measure'),required=True,default=1.0)
    bonus = fields.Float('Bonus',digits=dp.get_precision('Product Unit of Measure'),required=True)
