# Copyright (C) .

{
    'name': 'Task Time Advanced - Real Time Duration',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Real-time task duration tracking with timesheet integration',
    'description': """
Task Time Advanced - Real Time Duration
======================================

This module provides real-time task duration tracking functionality:

* Start/Stop task timer with real-time duration display
* Systray timer widget showing current running task
* Kanban view timer widget for running tasks
* Automatic timesheet line creation when starting tasks
* End task wizard to finalize duration and add to timesheet
* Real-time duration updates in task form and kanban views

Features:
---------
* Real-time duration counter in systray
* Start/Stop buttons in task form and kanban
* Automatic timesheet integration
* Duration tracking with start/end timestamps
* User-friendly timer interface
    """,
    'author': 'Usama',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'hr_timesheet',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/sh_start_timesheet_views.xml',
        'views/sh_task_time_account_line_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sh_task_time_adv/static/src/js/systray_icon_menu.js',
            'sh_task_time_adv/static/src/js/kanban_field_timer.js',
            'sh_task_time_adv/static/src/xml/time_track.xml',
            'sh_task_time_adv/static/src/scss/time_track.scss',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
