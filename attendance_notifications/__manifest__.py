{
    'name': 'Attendance Notifications',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Send email notifications for employee check-in and check-out',
    'description': """
        This module sends email notifications when employees check in or check out.
        Features:
        - Email notification on employee check-in
        - Email notification on employee check-out
        - Customizable email templates
        - Automatic email sending
    """,
    'author': 'Codex',
    'website': '',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'mail',
    ],
    'data': [
        'data/attendance_email_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 