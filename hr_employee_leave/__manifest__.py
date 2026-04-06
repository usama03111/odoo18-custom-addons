# -*- coding: utf-8 -*-
{
    'name': "HR Employee Leave",
    'summary': "Employee can request from Portal | Employee can view their backend details",

    'author': "Usama Wazir",
    'category': 'Portal',
    'version': '18.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'portal',],

    # always loaded
    'data': [
        'views/hr_employee_attendance.xml',
        'views/hr_employee_attendance_templete.xml',

    ],
    'images': ['static/description/banner.png'],

    'assets': {
    'web.assets_frontend': [
        'hr_employee_leave/static/src/css/hr_employee_attendance.css',
    ],
},

}
