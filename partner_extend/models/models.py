# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerInherit(models.Model):
    _inherit = 'res.partner'


    owner = fields.Char(string="", required=False, )
    specialization = fields.Char(string="", required=False, )
    authorization_number = fields.Char(string="", required=False, )
    authorization_start = fields.Char(string="", required=False, )
    authorization_end = fields.Char(string="", required=False, )
    authorization_status = fields.Char(string="", required=False, )
    # bo_box = fields.Char(string="", required=False, )
