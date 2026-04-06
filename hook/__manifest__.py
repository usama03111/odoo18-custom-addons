# -*- coding: utf-8 -*-

{
    "name": "Hook",
    "version": "1.0",
    "author": "Osama",
    "category": "Project",
    "sequence": -100,
    "summary": "Task Approval System",
    "description": """odoo provide four type of hook""",
    "depends": ['contacts'],
    "data": [],
    'pre_init_hook':'test_pre_init_hook',
    # 'post_init_hook':'',
    # 'uninstall_hook':'',
    # 'post_load':'',
    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
