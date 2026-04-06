# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def action_project_xls_entry(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sh_all_in_one_pms.sh_project_details_report_wizard_form_action')
        # Force the values of the move line in the context to avoid issues
        ctx = dict(self.env.context)
        ctx.pop('active_id', None)
        ctx['active_ids'] = self.ids
        ctx['active_model'] = 'account.move'
        action['context'] = ctx
        return action
