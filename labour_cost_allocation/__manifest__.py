{
    'name': 'Labour Cost Allocation',
    'version': '1.0',
    'summary': 'Allocate labour costs to projects via payslips',
    'description': 'Automatically creates analytic entries for labour costs upon payslip confirmation.',
    'author': 'Usama Wazir',
    'category': 'Human Resources',
    'depends': ['hr_payroll', 'project', 'account', 'analytic'],
    'data': [
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
