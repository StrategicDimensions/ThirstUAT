# -*- coding: utf-8 -*-
{
    'name' : 'i-Pay',
    'version' : '1.0',
    'depends' : ['payment','website_sale'],
    'author' : 'Strategic Dimensions',
    'category': 'payment',
    'summary':"i-pay",
    'description': """
    i-pay
    """,
    'website': 'http://www.odoo.com',    
    'data': [
	'views/ipay_template.xml',
	'data/ipay_data.xml',
	
    ],
    'demo': [],
    'installable': True,
    'application':True,
    'auto_install': False,
    
}
