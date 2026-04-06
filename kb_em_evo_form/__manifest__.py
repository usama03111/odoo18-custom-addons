# -*- coding: utf-8 -*-
{
    "name": "Employee Manager Evaluation Form",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "HR sends an evaluation form to the employee's manager for feedback, manager submits back to HR.",
    "author": "KB",
    "license": "LGPL-3",
    "depends": ["hr", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/employee_evaluation_views.xml",
        "views/hr_employee_inherit.xml",
        "views/menu.xml",
    ],
    "application": False,
    "installable": True,
}
