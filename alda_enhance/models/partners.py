from odoo import models, fields, api,exceptions
from odoo.tools.translate import _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    taxid = fields.Char(string="Tax ID")