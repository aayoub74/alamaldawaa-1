# -*- encoding: utf-8 -*-


from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp

#
# class res_partner(models.Model):
#     _inherit = "res.partner"
#
#     signature_image = fields.Binary('Signature',
#                                     help="La signature de l entreprise, limité à 1024x1024px."),

class res_users_inherited(models.Model):
    _name = "res.users"
    _inherit = "res.users"

    signature_img = fields.Binary("Signature", help="La signature de l'entreprise, limité à 1024x1024px.")
