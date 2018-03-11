# -*- coding: utf-8 -*-
{
    'name': "Alam Aldawaa Enhance",

    'summary': """
        Alam Aldawaa Enhance""",

    'description': """
        Alam Aldawaa Enhance
    """,

    'author': "Eslam Youssef",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
        'product',
        'purchase',
        'base_action_rule',
        'product_expiry',
        'hr_contract',
        'sale',
<<<<<<< HEAD
        'sale_contract',
=======
        'bi_purchase_discount',
>>>>>>> 06963dd6358f463f778e7f248dc2ffa492701a7a
        ],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'wizard/lot_return_view.xml',
        'wizard/create_sale_order_view.xml',
        'wizard/scrap_wizard.xml',
        'views/views.xml',
        'data/email_templates.xml',
        'data/automated_actions.xml',
        'reports/invoice_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}