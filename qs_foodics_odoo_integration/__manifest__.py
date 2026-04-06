# -*- coding: utf-8 -*-
{
    "name": "Foodics Odoo Connector",
    "version": "1.0",
    "category": "Point Of Sale",
    "summary": "Sync data from foodics to odoo",
    "description": """
        With this application user will be able to sync branches, inventory transactions, purchase orders, payment methods, categories, products and orders from foodics to odoo.
        from date and to date functionality.
    """,
    'author': 'Quick Services Solutions',
    'website': "https://www.qs-solutions.com",
    'company': 'Quick Services Solutions',
    'maintainer': 'Quick Services Solutions',
    "support": "info@qs-solutions.com",
    "depends": ["account", "point_of_sale", "stock", "product", "mrp", "purchase"],
    "data": [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'wizard/message_view.xml',
        'views/connector_view.xml',
        'views/pos_session.xml',
        'views/branches_view.xml',
        'views/payment_methods_view.xml',
        'views/categories_view.xml',
        'views/pos_orders_view.xml',
        'views/analytic_account_foodics_branch_name.xml',
        'views/purchase_order_views.xml',
        'wizard/foodic_operation_views.xml'
    ],
    "live_test_url" : "",
    "application": True,
    "installable": True,
    "auto_install": False,
    'external_dependencies': {
        'python': ['aiohttp'],},
    "price": 1500,
    "currency": "USD",
    "images": ['static/description/explain.gif'],
    "license": "OPL-1",
}

