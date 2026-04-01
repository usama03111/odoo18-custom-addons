# -*- coding: utf-8 -*-

{
    'name': "Project Task Overdue",
    "version": "18.0.0.7",
    'author': 'usama wazir',
    'company': 'codex',
    'website': '',
    'summary': 'auto  mail',
    'license': 'LGPL-3',
    "description": """auto mail send when deadline is completed""",
    'depends': ['project'],
    'data': [
        'security/security.xml',
         'data/task_overdue_email_template.xml',
        'data/task_overdue_cron.xml',
    ],
    'images': [''],
    "auto_install": False,
    "installable": True,

}
