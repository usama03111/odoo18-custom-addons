# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Whether Data',
    'version' : '1.0',
    'summary': 'whether stored',
    'sequence': -99,
    'description': """""",
    'category': 'Productivity',
    'website': 'https://www.abcschool.com',
    'license': 'LGPL-3',
    'depends' : ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/weather_data_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
