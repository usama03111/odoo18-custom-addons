# -*- coding: utf-8 -*-
{
	'name': 'HR Employee Profile Self Service',
	'summary': 'Allow employees to manage their own HR profile (edit/update only their record)',
	'author': 'Custom',
	'website': '',
	'category': 'Human Resources/Employees',
	'version': '18.0.1.0.0',
	'license': 'LGPL-3',
	'depends': ['hr',],
	'data': [
		'security/security.xml',
		'views/hr_employee_view.xml',
		# 'data/data.xml',
	],
	'application': False,
	'installable': True,
} 