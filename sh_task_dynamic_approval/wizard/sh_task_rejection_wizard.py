# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api, _
from datetime import datetime


class TaskRejectionWizard(models.TransientModel):
    _name = 'sh.task.rejection.wizard'
    _description = 'Task Rejection Wizard'

    task_id = fields.Many2one('project.task', string="Task")
    reason = fields.Text(string="Rejection Reason", required=True)

    def action_reject(self):
        self.ensure_one()

        if self.task_id:
            self.task_id.write({
                'approval_state': 'rejected',
                'reject_reason': self.reason,
                'reject_by': self.env.user.id,
                'rejection_date': fields.Datetime.now(),
                'level': 0,
                'group_ids': False,
                'user_ids': False,
            })

            # Notify all assigned users (user_ids instead of user_id)
            if self.task_id.user_ids:
                template = self.env.ref('sh_task_dynamic_approval.email_template_task_rejected')
                for user in self.task_id.user_ids:
                    template.send_mail(self.task_id.id, force_send=True, email_values={
                        'email_to': user.email,
                        'email_from': self.env.user.email
                    })
                    self.env['bus.bus']._sendone(
                        user.partner_id,
                        'sh_notification_info',
                        {
                            'title': _('Task Rejected'),
                            'message': f'Your task {self.task_id.name} has been rejected'
                        }
                    )
