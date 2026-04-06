# -*- coding: utf-8 -*-

{
    "name": "Task Approvals",
    "version": "1.0",
    "author": "Osama",
    "category": "Project",
    "summary": "Task Approval System",
    "description": """
        Task Approval System with Multiple Approvers
        
        Features:
        - Sequential or parallel approval process
        - Multiple approvers support
        - Approval tracking and status management
        - Activity notifications for approvers
        - Portal user support for external approvers
    """,
    "depends": ["project", "mail", "portal"],
    "data": [
        'security/task_approval_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/mail_template_customer_approval.xml',
        'data/mail_activity_type_data.xml',
        'data/sequence_data.xml',
        'wizard/reason_wizard_view.xml',
        'views/task_request_view.xml',
        'views/task_approver_views.xml',
        'views/task_category_approver_views.xml',
        'views/project_task_new_templete.xml',
        # 'views/project_tasks.xml',
        # 'views/portal_templates.xml',

    ],

    "demo": [],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
