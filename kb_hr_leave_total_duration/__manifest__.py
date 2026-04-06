{
    'name': 'Leave Duration Calendar Days',
    'version': '18.0',
    'category': 'Human Resources',
    'summary': 'Toggle between working days and calendar days for leave duration',
    'description': """
        This module adds a boolean field to Leave Requests to allow calculation
        of duration based on calendar days instead of working days.
    """,
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
