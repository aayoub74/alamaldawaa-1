# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Default Warehouse Operations')

    product_category_ids = fields.Many2many(
        'product.category', 'product_category_users_rel',
        'user_id', 'product_category_id', string='Allowed Product Category')

    stock_route_ids = fields.Many2many(
        'stock.location.route', 'stock_location_route_users_rel',
        'user_id', 'stock_route_id', string='Restricted Routes')

    journal_ids = fields.Many2many(
        'account.journal', 'account_journal_users_rel',
        'user_id', 'journal_id', string='Restricted Journals')

    partner_ids = fields.Many2many(
        'res.partner', 'res_partner_users_rel',
        'user_id', 'partner_id', string='Restricted Partners'
    )

class resPartner(models.Model):
    _inherit = 'res.partner'
    users_ids = fields.Many2many('res.users','res_partner_users_rel','partner_id','user_id',
                                 string='Allowed Users')

class AccountJournal(models.Model):
    _inherit = 'account.journal'
    users_ids = fields.Many2many('res.users','account_journal_users_rel','journal_id','user_id',
                                 string='Allowed Users')

class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'
    users_ids = fields.Many2many('res.users','stock_location_route_users_rel','stock_route_id','user_id',
                                 string='Allowed Users')
class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.one
    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        if self.state == 'draft':
            return True
        user_locations = self.env.user.stock_location_ids
        if self.env.user.restrict_locations:
            message = _(
                'Invalid Location. You cannot process this move since you do '
                'not control the location "%s". '
                'Please contact your Adminstrator.')
            if self.location_id not in user_locations and self.location_id.usage == 'internal':
                raise Warning(message % self.location_id.name)
            elif self.location_dest_id not in user_locations and self.location_dest_id.usage == 'internal':
                raise Warning(message % self.location_dest_id.name)


