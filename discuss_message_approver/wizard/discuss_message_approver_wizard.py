from markupsafe import Markup
from odoo import fields, models, _
from odoo.exceptions import ValidationError

class DiscussMessageApproverWizard(models.TransientModel):
    _name = 'discuss.message.approver.wizard'
    _description = 'Create Task from Message'

    name = fields.Char(string='Task Name', required=True)
    approver_id = fields.Many2one('task.approver', string='Approver')
    date_deadline = fields.Date(string='Deadline')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    body = fields.Html(string='Description')
    message_id = fields.Many2one('mail.message', string='Original Message')

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        message_id = self.env.context.get('default_message_id') or self.env.context.get('message_id')
        if message_id and 'body' in fields_list:
            message = self.env['mail.message'].browse(message_id)
            if message:
                body_content = message.body or ''
                for attachment in message.attachment_ids:
                    if attachment.mimetype.startswith('image'):
                        body_content += Markup(f'<br/><img src="/web/image/{attachment.id}"/>')
                    else:
                        body_content += Markup(f'<br/><a href="/web/content/{attachment.id}">{attachment.name}</a>')
                res['body'] = body_content
        return res

    def action_create_task(self):
        self.ensure_one()
        task = self.env['project.task'].create({
            'name': self.name,
            'approver_id': self.approver_id.id,
            'date_deadline': self.date_deadline,
            'project_id': self.project_id.id,
            'description': self.body,
        })
        if self.message_id:
            self.message_id.approval_task_id = task.id

            # Make original attachments public so they can be viewed by portal users
            if 'public' in self.env['ir.attachment']:
                 self.message_id.attachment_ids.write({'public': True})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'form',
            'res_id': task.id,
            'target': 'new',
        }

