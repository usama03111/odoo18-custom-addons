# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models,fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    check_bool_enable_task_send_by_email = fields.Boolean(
        related="company_id.enable_task_send_by_email")

    def action_task_send_email(self):
        if self:
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                compose_form_id = ir_model_data._xmlid_to_res_id(
                    'mail.email_compose_message_wizard_form')
            except ValueError:
                compose_form_id = False
            try:
                template_id = ir_model_data._xmlid_to_res_id(
                    'sh_all_in_one_pms.sh_task_mail_template_attachment')
                attachment_ids = []
                if self.attachment_ids:
                    attachment_ids = self.attachment_ids.ids
                ctx = {
                    'default_model': 'project.task',
                    'default_res_ids': self.ids,
                    'default_use_template': bool(template_id),
                    'default_template_id': template_id,
                    'default_attachment_ids':[(6,0,attachment_ids)],
                    'default_composition_mode': 'comment',
                    'force_email': True,
                }
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form_id, 'form')],
                    'view_id': compose_form_id,
                    'target': 'new',
                    'context': ctx,
                }
            except ValueError:
                template_id = False
