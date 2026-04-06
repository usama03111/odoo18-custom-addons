# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Project Team Management",

    "author": "Softhealer Technologies",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "16.0.1",

    "category": "Project",

    "license": "OPL-1",

    "summary": "Project With Project Team Create Project Team Project Task Team Sub Task Team Projects Team Management Project Team On Project Task Team Based Project Access Divide Projects With Team Retariction On Task Restriction On Project Restriction Odoo",

    "description": """Do you want to manage the project team in project? This module allows you to create and manage project team with team leaders & team members. You can select the project team in the project and their task. You can group by project with the project team. Project team displayed in kanban view & list view of the project & task.""",

    "depends": ['project'],
    "data": [
            'security/sh_project_team_security.xml',
            'security/ir.model.access.csv',
            'views/sh_project_team.xml',
            'views/project_views.xml',
    ],
    "application": True,
    "auto_install": False,
    "installable": True,
    "images": ["static/description/background.png", ],
    "price": "20",
    "currency": "EUR"
}
