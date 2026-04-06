# -*- coding: utf-8 -*-
{
    'name': 'HR Employee Access',
    'version': '18.0.1.0.0',
    'category': 'HR',
    'sequence': 25,
    'summary': ' ',
    'author': 'Irfan Ullah',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'hr_skills'],

    'data': [
        'security/employee_custom_groups.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_inherit.xml',
    ],
}