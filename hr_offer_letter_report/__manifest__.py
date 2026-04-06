{
    'name': 'HR Contract Report',
    'version': '1.0',
    'category': 'Human Resources/Contracts',
    'summary': 'Printable employment contract and offer letter report.',
    'description': """
HR Contract Report

This module provides a professionally formatted PDF report for:

- Employment Contracts
- Offer Letters
- Compensation Details
- Probation Period
- HR Policies
- Offer Validity

Designed to work with the HR Contract Compensation module.
""",
    'depends': [
        'hr_contract',
        'hr_contract_compensation',
    ],
    'data': [
        'reports/contract_offer_report.xml',
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
