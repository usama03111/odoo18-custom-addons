# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Air Ticket Allocation',
    'version': '1.0',
    'category': 'Human Resources/Holidays',
    'summary': 'Separate Air Ticket Allocations from Paid Time Off on Employee form',
    'description': """
This module adds a flag on allocations to distinguish "Air Ticket" from standard "Paid Time Off".
It splits the "Time Off" smart button on the employee form into two distinct buttons: one for Paid Time Off and one for Air Ticket.
    """,
    'depends': ['hr_holidays' , 'hr_contract_compensation'],
    'data': [
        'views/hr_leave_allocation_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
