from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    basic = fields.Integer('Basic')
    variable = fields.Integer('Variable')
    accom = fields.Integer('Accommodation')
    trans = fields.Integer('Transportation')
    mobi = fields.Integer('Mobile')