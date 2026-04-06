# Copyright (C) Softhealer Technologies.

from odoo import models, fields,_
from datetime import datetime

class TaskTimeAccountLine(models.Model):
    _name = 'sh.task.time.account.line'
    _description = 'Task Time Account Line'

    def _get_default_start_time(self):
        if self.env.user.task_id:
            return self.env.user.start_time

    def _get_default_end_time(self):
        return datetime.now()

    def _get_default_duration(self):
        active_model = self.env.context.get('active_model')
        if active_model == 'project.task':
            active_id = self.env.context.get('active_id')
            if active_id:
                task_search = self.env['project.task'].search(
                    [('id', '=', active_id)], limit=1)
                diff = fields.Datetime.from_string(fields.Datetime.now(
                )) - fields.Datetime.from_string(self.env.user.start_time)
                if diff:
                    duration = float(diff.days) * 24 + \
                        (float(diff.seconds) / 3600)
                    return round(duration, 2)

    name = fields.Text("Description", required=True)
    start_date = fields.Datetime(
        "Start Date", default=_get_default_start_time, readonly=True)
    end_date = fields.Datetime(
        "End Date", default=_get_default_end_time, readonly=True)
    duration = fields.Float(
        "Duration (HH:MM)", default=_get_default_duration, readonly=True)

    def end_task(self):

        context = dict(self.env.context or {})
        active_model = context.get('active_model', False)
        active_id = context.get('active_id', False)

        vals = {'name': self.name, 'unit_amount': self.duration,
                'amount': self.duration, 'date': datetime.now()}

        if active_model == 'project.task':
            if active_id:
                task_search = self.env['project.task'].search(
                    [('id', '=', active_id)], limit=1)

                if task_search:
                    vals.update({'end_date': datetime.now()})
                    vals.update({'task_id': task_search.id})

                    if task_search.project_id:
                        vals.update({'project_id': task_search.project_id.id})
                        # Get analytic account from project
                        if hasattr(task_search.project_id, 'analytic_account_id') and task_search.project_id.analytic_account_id:
                            vals.update({'account_id': task_search.project_id.analytic_account_id.id})

                    task_search.sudo().write({'start_time': None,'task_running': False, 'task_runner':False})
                    if self.name:
                        task_search.sudo().message_post(
                            body=_(f"Description: {self.name}"),
                            message_type="comment",
                            subtype_xmlid="mail.mt_note",
                        )
        timesheet_line = self.env['account.analytic.line'].sudo().search(
            [('task_id', '=', task_search.id), ('employee_id.user_id',
                                                    '=', self.env.uid),('end_date', '=', False)], limit=1)
        if timesheet_line:
            timesheet_line.write(vals)
        self.sudo()._cr.commit()
        self.env.user.write({'task_id': False})

        return {'type': 'ir.actions.client', 'tag': 'reload'}
