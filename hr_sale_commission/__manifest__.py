# -*- coding: utf-8 -*-
{
    'name': "hr_sale_commission",

    'summary': """
        Adding Employee Sale Commission based on Journal 
        defiend for every Users""",

    'description': """
        Adding Employee Sale Commission based on Journal 
        defiend for every Users
    """,

    'author': "TryIT",
    'website': "https://tryit.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'alda_enhance',
                'warehouse_stock_restrictions',
                'hr',
                'hr_payroll',
                ],

    'installable':True,

    # always loaded
    'data': [
        'views/hr_views.xml',
        'data/hr_salary_rule.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}