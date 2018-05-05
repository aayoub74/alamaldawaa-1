# -*- coding: utf-8 -*-
from odoo import http

# class HrSaleCommission(http.Controller):
#     @http.route('/hr_sale_commission/hr_sale_commission/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_sale_commission/hr_sale_commission/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_sale_commission.listing', {
#             'root': '/hr_sale_commission/hr_sale_commission',
#             'objects': http.request.env['hr_sale_commission.hr_sale_commission'].search([]),
#         })

#     @http.route('/hr_sale_commission/hr_sale_commission/objects/<model("hr_sale_commission.hr_sale_commission"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_sale_commission.object', {
#             'object': obj
#         })