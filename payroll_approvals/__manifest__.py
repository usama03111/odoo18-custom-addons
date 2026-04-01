# -*- coding: utf-8 -*-

{
    "name": "Payroll Approvals",
    "version": "1.0",
    "author": "Osama",
    "category": "Payroll",
    "sequence": -100,
    "summary": "Payroll Approval System",
    "description": """
        Payroll Approval System with Multiple Approvers
        
        Features:
        - Sequential or parallel approval process
        - Multiple approvers support
        - Approval tracking and status management
        - Activity notifications for approvers
    """,
    "depends": ["hr_payroll_community",],
    "data": [
        'security/ir.model.access.csv',
        'data/mail_activity_type_data.xml',
        'wizard/reason_wizard_view.xml',
        'views/hr_payroll_request_view.xml',
        'views/hr_payslip_batches_request_view.xml',
        'views/payroll_approver_views.xml',
        'views/payroll_category_approver_views.xml',


    ],

    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
