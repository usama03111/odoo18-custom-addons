{
    'name': 'HR Employee Salary Certificate Report',
    'version': '1.0',
    'category': 'Human Resources/Employees',
    'summary': 'Printable Salary Certificate report for employees.',
    'description': """
HR Employee Salary Certificate Report

This module provides a professionally formatted PDF Salary Certificate report
for employees. It pulls data from the employee record and their active contract
including salary breakdown (basic, allowances, gross).

Designed to work with the HR Contract Compensation module.
""",
    'depends': [
        'hr',
        'hr_contract',
        'hr_contract_compensation',
    ],
    'data': [
        'reports/employee_salary_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
