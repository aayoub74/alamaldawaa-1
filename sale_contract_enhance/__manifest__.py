# -*- coding: utf-8 -*-
{
    'name': "Sale Contract Enhance",

    'summary': """
        Sale Contract Enhance""",

    'description': """
        This Module was created to override and fix a function which gives an error 
    """,

    'author': "Mohamed sharaf",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'sale_contract',
        'website_contract',

    ],

    # always loaded
    'data': [
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
