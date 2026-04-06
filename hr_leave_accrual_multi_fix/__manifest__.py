{
    'name': 'HR Leave Accrual Multi Wizard Fix',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Fixes accrual plan selection in the multi-employee allocation wizard',
    'description': """
        When creating time off allocations for multiple employees via the
        "Generate Multiple Allocations" wizard, selecting an accrual plan
        does not correctly update the description or reset the duration to 0.
        
        This module fixes the behavior to match the single-employee allocation form.
    """,
    'author': 'usama',
    'depends': ['hr_holidays'],
    'data': [
        'wizard/hr_leave_allocation_generate_multi_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
