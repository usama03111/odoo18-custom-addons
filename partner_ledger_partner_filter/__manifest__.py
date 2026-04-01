# -*- coding: utf-8 -*-
{
    'name': 'Partner Ledger Smart Filter',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Filter Partner Ledger report by selected partners',
    'description': """
Partner Ledger Smart Filter
===========================
This module enhances the Partner Ledger report from Base Accounting Kit.

Features:
- Allows selecting multiple partners in the Partner Ledger filter.
- Displays the report only for selected partners.
- Preserves the order of selected partners in the report output.
- Useful for accountants and finance teams who need focused partner statements.

Dependency:
- base_accounting_kit
    """,
    'author': 'codex',
    'website': '',
    'depends': [
        'base_accounting_kit',
    ],
    'data': [
        # Add your XML files here if you have any (views, wizards, reports)
        'views/account_report_partner_ledger_m2m_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
