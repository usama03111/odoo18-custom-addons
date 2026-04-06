{
    'name': 'Password Manager',
    'version': '1.0',
    'summary': 'Securely store and share credentials',
    'description': """
        Password Manager Module
        - securely store credentials
        - Encrypted passwords
        - Strict access control
        - Audit trail for access
    """,
    'category': 'Tools',
    'author': 'Usama Wazir',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/password_entry_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
             'password_manager/static/src/js/password_clipboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
