from odoo import models, fields, api


class TaskRefuseWizardReason(models.TransientModel):
    _name = 'task.refuse.wizard.reason'
    _description = 'Task Refuse Wizard Reason'

    reason = fields.Text('Reason', required=True)

    def action_refuse(self):
        task = self.env['project.task'].browse(self._context.get('active_id'))
        task.action_cancel()
        task.write({'rejection_reason': self.reason})

