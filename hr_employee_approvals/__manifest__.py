{
    'name': 'HR Employee Approvals',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Add approval workflow to Employee creation',
    'description': """
        This module adds an approval workflow to the HR Employee model.
        It allows defining a sequence of approvers for new employee records.
    """,
    'author': 'usama',
    'depends': ['hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
