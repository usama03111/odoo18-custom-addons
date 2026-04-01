{
    'name': 'Discuss Message Approver',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Add Approver option to Discuss messages',
    'depends': ['mail', 'web', 'project', 'odoo_task_approvals'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/discuss_message_approver_wizard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'discuss_message_approver/static/src/js/message_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
