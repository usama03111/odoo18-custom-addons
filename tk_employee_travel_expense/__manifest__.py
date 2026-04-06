# -*- coding: utf-8 -*-
{
    'name': 'Employee Travel Expense',
    'description': """
           Employee Travel Expense
    """,
    'summary': 'Employee Travel Expense',
    'version': '1.0',
    'category': 'Customer',
    'author': 'TechKhedut Inc.',
    'company': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'website': "https://www.techkhedut.com",
    'depends': [
        'hr',
        'mail',
        'account',
        'project',
        'hr_expense',
    ],
    'data': [
        # Security
        'security/security_access.xml',
        'security/ir.model.access.csv',
        # data
        'data/sequence.xml',
        'data/employee_travel_request_rejected_mail.xml',
        # wizard
        'wizard/travel_request_reject_view.xml',
        # report
        'report/employee_travel_request_report.xml',
        # Views
        'views/departure_mode.xml',
        'views/hr_expense_view.xml',
        'views/request_reject_reason.xml',
        'views/employee_travel_request.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/cover.png'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
