# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    "name": "Payment Installments",
    "version": "18.0.1.0",
    "category": "Accounting/Accounting",
    "summary": """
        This module is used to make payments in installment wise in sales, user can set Tenure months, Tenure amount and can Compute and Part Payment in Installment and Print sale order and Invoice Reports.
    """,
    "description": """
This module provides to make payments in installments
=====================================================


    """,
    "license": "OPL-1",
    "author": "Kanak Infosystems LLP.",
    "website": "http://www.kanakinfosystems.com",
    "depends": ["sale_management", "account", "stock", "sales_team"],
    "data": [
        "data/data.xml",
        "data/demo.xml",
        "security/ir.model.access.csv",
        "wizard/create_part_payment.xml",
        "views/payment_installment_view.xml",
        "views/res_config_settings_views.xml",
        "views/sale_installment_report.xml",
        "views/payment_term.xml",
        "views/invoice_installment_report.xml",
        "views/report_sale_installment.xml",
    ],
    'assets': {
        'web.assets_backend': ['payment_installment_kanak/static/src/css/backend.css'],
    },
    "images": ["static/description/banner.jpg"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "price": 70,
    "currency": "USD",
}
