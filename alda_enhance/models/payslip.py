from odoo import models, fields, api, exceptions
from odoo.tools.translate import _


class NewModule(models.Model):
    _inherit = 'hr.payslip'

    allowance_amount = fields.Float(string="", required=False, )
    deduction_amount = fields.Float(string="", required=False, )
