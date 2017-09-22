# -*- coding: utf-8 -*-
from odoo import http

# class AldaProduct(http.Controller):
#     @http.route('/alda_product/alda_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/alda_product/alda_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('alda_product.listing', {
#             'root': '/alda_product/alda_product',
#             'objects': http.request.env['alda_product.alda_product'].search([]),
#         })

#     @http.route('/alda_product/alda_product/objects/<model("alda_product.alda_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('alda_product.object', {
#             'object': obj
#         })