# -*- coding: utf-8 -*-

{
    'name': "Customer Overdue Reminder",
    "version": "18.0.0.6",
    'author': '',
    'company': 'codex',
    'website': '',
    'summary': 'Adds overdue payment reminder settings on customers',
    'license': 'LGPL-3',
    "description": """auto mail send when overdue is completed""",
    'depends': ['account','base'],
    'data': [
        'views/res_partner_view.xml',
        'data/cron.xml',

    ],
    'images': [''],
    "auto_install": False,
    "installable": True,

}
