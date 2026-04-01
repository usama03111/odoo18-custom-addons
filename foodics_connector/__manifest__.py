
# -*- coding: utf-8 -*-
{
    'name': "Foodics Connector",
    'version': '18.0.1.0.0',
    'summary': 'Foodics OAuth 2.0 Integration',
    'description': """
Foodics OAuth 2.0 Connector
===========================
This module handles the OAuth 2.0 Authorization Code flow for Foodics.
It captures the authorization code from the redirect URL and exchanges it for access and refresh tokens.
    """,
    'author': "usama",
    'category': 'Tools',
    'depends': ['base', 'web', 'website', 'auth_signup', 'qs_foodics_odoo_integration'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
