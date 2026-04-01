from odoo import models, fields, api


class TaskRefuseWizardReason(models.TransientModel):
    _name = 'payroll.refuse.wizard.reason'
    _description = 'Task Refuse Wizard Reason'

    reason = fields.Text('Reason', required=True)

    # def action_refuse(self):
    #     task = self.env['hr.payslip'].browse(self._context.get('active_id'))
    #     task.action_cancel()
    #     task.write({'rejection_reason': self.reason})

    def action_refuse(self):
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        record = self.env[active_model].browse(active_id)
        record.action_cancel()
        record.write({'rejection_reason': self.reason})
