# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Payment(models.Model):
    _inherit = 'account.payment'

    cancelled_before = fields.Boolean("Cancelled Before", default=False)

    @api.multi
    def cancel(self):
        res = super(Payment, self).cancel()
        for r in self:
            r.cancelled_before = True
        return res

    @api.multi
    def post(self):
        for r in self:
            if r.cancelled_before and \
                    not (self.env.user.has_group('alda_enhance.alda_gm') or
                         self.env.user.has_group('alda_enhance.alda_cfo')) and \
                    r.payment_type == 'inbound':
                raise ValidationError(_("You Don't have permission to reconfirm this payment"))
        return super(Payment, self).post()
