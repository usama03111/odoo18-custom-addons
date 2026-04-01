# -*- coding: utf-8 -*-
{
    'name': 'Discuss: General Channel Restrict Posting',
    'version': '18.0.1.0.0',
    'summary': 'General channel visible to all, only specific group can post',
    'description': 'Keeps General channel visible to everyone while restricting posting rights to a defined security group.',
    'author': 'Codex',
    'website': '',
    'category': 'Discuss',
    'license': 'LGPL-3',
    'depends': ['mail', 'web'],
    'data': [
        'security/general_post_group.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'oh_discuss_general_restrict/static/src/js/rpc_error_notification.js',
        ],
        'mail.assets_discuss': [
            '/oh_discuss_general_restrict/static/src/js/rpc_error_notification.js',
        ],
    },
    'installable': True,
    'application': False,
} 