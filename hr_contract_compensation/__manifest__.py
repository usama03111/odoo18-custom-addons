{
    'name': 'HR Contract Extension',
    'version': '1.0',
    'summary': 'Extends employee contracts with compensation structure, allowances, deductions, and cost calculations.',
    'description': """
HR Contract Extension

This module enhances employee contracts by adding:

- Allowances (Phone, Food, HRA, Transportation, etc.)
- Deductions
- Monthly & Yearly Cost computation
- Probation Period
- Offer Validity
- HR Policy fields (Airfare, Vacation, Medical, Governing Law)

It provides a structured compensation model within contracts.
""",
    'author': 'Usama Wazir',
    'category': 'Human Resources/Contracts',
    'depends': [
        'hr_contract',
        'hr_payroll',
    ],
    'data': [
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
}
