# -*- coding: utf-8 -*-

{
    'name': 'Project Scrum Management Agile Methodology',
    'version': '18.0.0.0.1',
    'summary': """ Project Scrum Management Agile Methodology""",
    'category': 'Project Management',
    'description': """Project Scrum Management Agile Methodology""",
    'author': 'TIT Solutions',
    "support": "sogesi@sogesi-dz.com",
    'website': "https://sogesi-dz.com/",
    'sequence': 0,
    'depends': ['base_setup', 'project', 'hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'views/sprint_stage_view.xml',
        'views/scrum_us_view.xml',
        'views/project_task_view.xml',
        'views/scrum_sprint_view.xml',
        'views/scrum_meeting_view.xml',
        'views/scrum_case_view.xml',
        'views/project_project_view.xml',
        'views/menu_view.xml',
        'views/email_template.xml',

    ],
    'license': 'OPL-1',
    'price' : '139.00',
    'currency' : 'EUR',
    'images': ["static/description/banner.png"],
    'installable': True,
    'auto_install': False,
    'application': False,
}
