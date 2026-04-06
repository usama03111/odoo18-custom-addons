# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models


class ProjectTask(models.Model):
    _inherit = "project.task"

    def action_project_task_xls_entry(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sh_project_task_print.sh_project_task_details_report_wizard_form_action')
        # Force the values of the move line in the context to avoid issues
        ctx = dict(self.env.context)
        ctx.pop('active_id', None)
        ctx['active_ids'] = self.ids
        ctx['active_model'] = 'account.move'
        action['context'] = ctx
        return action
