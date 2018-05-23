# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Beverages',
    'version': '1.0',
    'category': 'Beverages',
    'sequence': 20,
    'images' : ['images/icon.png'],
    'description': """ Beverages Settings and Configurations""",
    'website': 'http://www.strategicdimensions.co.za/',
    'depends': ['base','sale', 'account', 'procurement', 'report', 'web_tour'],
    'data': [
        'security/ir.model.access.csv',
        'views/beverages.xml',
    ],
    #'css': ['static/src/css/sale.css'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
