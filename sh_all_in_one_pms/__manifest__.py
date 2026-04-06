# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All In One PMS | Project Management System | All-in-One PMS system",

    'author': 'Softhealer Technologies',

    'website': 'https://www.softhealer.com',

    "support": "support@softhealer.com",

    'version': '0.0.1',

    "license": "OPL-1",

    'category': "Project",

    'summary': "Update Project Stage,Overdue Task Email,Project Checklist,Project Priority,Task Priority,Auto Project Task Stage,Task To Multiple User,Print Project Report,Task Auto Assign,Task Checklist,Task Custom Field,Update Task,Task Subtask,Task Timer odoo,Project Team Management",

    'description': """Are you still managing all projects and tasks with separate modules? That’s really a waste of time and effort. Our module, all-in-one project management system (PMS) focused on managing every aspect of your projects. You can handle projects, tasks, due dates, checklists etc in one module. All in one PMS makes it easier to manage all projects and tasks. So go ahead and download the module to improve your project management skills!""",
    'depends': [
        'base_setup', 'project', 'mail', 'hr_timesheet',
        'analytic', 'sh_message', 'sh_base_document',
    ],
    "data": [
        "sh_overdue_task_email_notification/data/sh_over_due_task_notification_data.xml",
        "sh_overdue_task_email_notification/data/sh_overdue_task_email_notification_templates.xml",
        "sh_overdue_task_email_notification/security/ir.model.access.csv",
        "sh_overdue_task_email_notification/views/sh_project_task_overdue.xml",

        'sh_task_custom_checklist/security/task_checklist_security.xml',
        'sh_task_custom_checklist/security/sh_task_custom_checklist_groups.xml',
        'sh_task_custom_checklist/security/ir.model.access.csv',
        'sh_task_custom_checklist/wizard/sh_import_task_wizard_views.xml',
        'sh_task_custom_checklist/views/sh_task_checklist_views.xml',
        'sh_task_custom_checklist/views/sh_task_checklist_template_views.xml',
        'sh_task_custom_checklist/views/project_task_views.xml',

        "sh_task_cl/security/task_checklist_rule.xml",
        "sh_task_cl/security/ir.model.access.csv",
        "sh_task_cl/security/sh_task_checklist_groups.xml",
        "sh_task_cl/wizard/sh_import_task_wizard_views.xml",
        "sh_task_cl/views/sh_task_checklist_views.xml",
        "sh_task_cl/views/project_task_views.xml",

        'sh_task_send_email/data/project_task_data.xml',
        'sh_task_send_email/views/project_task_views.xml',

        "sh_task_custom_fields/security/sh_task_custom_field_groups.xml",
        "sh_task_custom_fields/security/ir.model.access.csv",
        "sh_task_custom_fields/views/sh_custom_model_task_views.xml",
        "sh_task_custom_fields/views/sh_custom_tab_task_views.xml",
        "sh_task_custom_fields/views/project_task_views.xml",
        "sh_task_custom_fields/views/sh_custom_model_task_menus.xml",
        "sh_task_custom_fields/views/sh_custom_tab_task_menus.xml",

        'sh_task_mass_update/security/ir.model.access.csv',
        'sh_task_mass_update/data/project_task_data.xml',
        'sh_task_mass_update/wizard/sh_project_task_mass_update_wizard_views.xml',

        'sh_task_time_adv/security/ir.model.access.csv',
        'sh_task_time_adv/views/sh_start_timesheet_views.xml',
        'sh_task_time_adv/views/sh_task_time_account_line_views.xml',
        'sh_task_time_adv/views/project_task_views.xml',

        'sh_task_auto_asssign_stage/views/project_task_type_views.xml',

        'sh_project_stages/security/ir.model.access.csv',
        'sh_project_stages/security/sh_project_stages_groups.xml',
        'sh_project_stages/data/project_project_data.xml',
        'sh_project_stages/views/project_project_views.xml',
        'sh_project_stages/views/sh_project_stage_template.xml',
        'sh_project_stages/wizard/sh_project_mass_update_wizard_views.xml',

        'sh_mass_project_stage/security/ir.model.access.csv',
        'sh_mass_project_stage/data/project_task_type_data.xml',
        'sh_mass_project_stage/wizard/sh_mass_stage_update_wizard_views.xml',

        'sh_project_priority/views/project_task_views.xml',
        'sh_project_priority/views/project_project_views.xml',

        'sh_project_custom_checklist/security/ir.model.access.csv',
        'sh_project_custom_checklist/security/sh_project_custom_checklist_groups.xml',
        'sh_project_custom_checklist/data/sh_project_custom_checklist_data.xml',
        'sh_project_custom_checklist/wizard/sh_import_project_custom_cl_wizard_views.xml',
        'sh_project_custom_checklist/views/sh_project_custom_checklist_views.xml',
        'sh_project_custom_checklist/views/sh_project_custom_checklist_menus.xml',
        'sh_project_custom_checklist/views/sh_project_custom_checklist_template_views.xml',
        'sh_project_custom_checklist/views/sh_project_custom_checklist_template_menus.xml',
        'sh_project_custom_checklist/views/project_project_views.xml',

        'sh_project_document/security/sh_project_document_groups.xml',
        'sh_project_document/data/sh_project_document_mail_templates.xml',
        'sh_project_document/data/sh_project_document_data.xml',
        'sh_project_document/views/project_project_views.xml',
        
        'sh_task_document/security/sh_task_document_groups.xml',
        'sh_task_document/data/ir_attachment_mail_templates.xml',
        'sh_task_document/data/ir_attachment_data.xml',
        'sh_task_document/views/project_task_views.xml',
        
        "sh_project_category/security/ir.model.access.csv",
        "sh_project_category/security/sh_project_catagory_groups.xml",
        "sh_project_category/views/project_category_views.xml",

        "sh_project_task_print/security/ir.model.access.csv",
        "sh_project_task_print/report/project_task_templates.xml",
        "sh_project_task_print/report/project_project_templates.xml",
        "sh_project_task_print/wizard/project_task_xls_report_wizard.xml",
        "sh_project_task_print/wizard/project_xls_report_wizard.xml",

        'sh_project_milestone/views/project_project_views.xml',
        'sh_project_milestone/views/project_task_views.xml',
        'sh_project_milestone/views/report_project_task_user_views.xml',
        'sh_project_milestone/views/project_milestone_views.xml',
        'sh_project_milestone/views/project_milestone_menus.xml',

        'sh_project_team/security/ir.model.access.csv',
        'sh_project_team/security/sh_project_team_security.xml',
        'sh_project_team/views/project_views.xml',
        'sh_project_team/views/sh_project_team.xml',

        'sh_custom_project_template/security/project_template_security.xml',
        'sh_custom_project_template/security/ir.model.access.csv',
        'sh_custom_project_template/views/res_config_settings_views.xml',
        'sh_custom_project_template/views/project_template_views.xml',
        'sh_custom_project_template/views/project_template_task_views.xml',
        'sh_custom_project_template/views/project_project_views.xml',

        'views/all_res_config_settings.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'web/static/src/js/ajax.js',
            'sh_all_in_one_pms/static/src/js/kanban_field_timer.js',
            'sh_all_in_one_pms/static/src/js/systray_icon_menu.js',
            'sh_all_in_one_pms/static/src/scss/time_track.scss',
            'sh_all_in_one_pms/static/src/xml/time_track.xml',
        ],
    },
    'demo': [],
    'installable':
    True,
    'application':
    True,
    'auto_install':
    False,
    'images': ['static/description/background.gif', ],
    "price": 150,
    "currency": "EUR"
}
