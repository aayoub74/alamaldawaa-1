# -*- encoding: utf-8 -*-

{
    'name': 'Electronic signature',
    'version': '1.0',
#     'depends': ['account'],
    "author" : "Odoo Tips",
    'currency': 'EUR',
    'price': 4.99,
    'sequence': 150,
    "website" : "http://www.gotodoo.ma",
    'description': "Insert the electronic signature to the (Invoice, Sale Order, Purchase Order) reports",
    'category': 'Tools',
    'depends' : [
                    'account','sale','purchase',
                ],
    'images': ['images/main_screenshot.png'],
    'data' : [
              'views/report_invoice.xml',
              'views/report_saleorder.xml',
              'views/report_purchaseorder.xml',
              'views/res_users_view.xml',
               ],
     
  
    'application': True,
    'installable': True

}


