# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp

class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '%s [%s]' % (name,code)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []
        for product in self.sudo():
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
                if not sellers:
                    sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
    

class ProductInher(models.Model):

    _inherit = 'product.template'

    pharma_form = fields.Char(
        string='Pharmaceutical Form',
    )

    container = fields.Char(
        string='Container',
    )
    container_vol = fields.Float(
        string='Container Volume',
        digits=(16,2),
    )
    conc = fields.Char(
        string='Conc',
    )
    conc_unit = fields.Char(
        string='Conc Unit',
    )
    storage_conditions = fields.Char(
        string='Storage Conditions',
    )

    manufacturer = fields.Char(
        string='Manufacturer',
    )
    origin = fields.Char(
        string='Origin',
    )
    agent = fields.Char(
        string='Agent',
    )
    marketing_company = fields.Char(
        string='Marketing Company',
    )

    sale_discount = fields.Float(string='Sale Discount1(%)',digits=dp.get_precision('Discount'))
    sale_discount2 = fields.Float(string='Sale Discount2(%)',digits=dp.get_precision('Discount'))

    @api.one
    @api.constrains('sale_discount','sale_discount2')
    def _check_discount(self):
        if self.sale_discount > 100 or self.sale_discount < 0 or \
                        self.sale_discount2 > 100 or self.sale_discount2 < 0:
            raise exceptions.ValidationError(_("Sale Discount Must be between 0.00 and 100.00"))

    @api.one
    @api.constrains('life_time', 'use_time', 'alert_time', 'removal_time')
    def _check_dates(self):
        dates = filter(lambda x: x, [self.removal_time ,self.alert_time])
        sort_dates = list(dates)
        sort_dates.sort()
        if dates != sort_dates:
            raise exceptions.UserError(
                _('Dates must be: Removal Time < Alert Time'))

    @api.multi
    def name_get(self):
        return [(template.id, '%s%s' % (template.name,template.default_code and '[%s] ' % template.default_code or ''))
            for template in self]


