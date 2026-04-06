# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api
import datetime

class ProjectTaskOverdueEmail(models.Model):
    _name = "sh.project.task.overdue.email"
    _description = 'Project Task Overdue Email'

    name = fields.Char("Task")
    user_ids = fields.Many2many("res.users",string="Email Users")
    company_id = fields.Many2one(
        "res.company",
        "Company Id",
        default=lambda self: self.env.user.company_id
    )
    notify_ids = fields.One2many("sh.project.task.overdue.notify","email_id","Notify Id")

    @api.model
    def notify_employee_overdue_fun(self):
        company_object = self.env['res.company'].search([])
        if company_object:
            notify = self.env['sh.project.task.overdue.notify'].search([])
            if notify:
                notify.unlink()
            for comp_rec in company_object:
                if comp_rec.notification:
                    over_due_days = comp_rec.overdue_days
                    date_check = (fields.datetime.now() -
                                  datetime.timedelta(over_due_days))
                    users = self.env['res.users'].sudo().search([])

                    user_wise_overdue_task = {}
                    if users:

                        for user in users:
                            line_list = []
                            task_search = self.env['project.task'].search([('user_ids.id','in',user.ids),('company_id','in', [False] + comp_rec.ids),('completed','=',False),('date_deadline','<=',date_check.date())])
                            if task_search :
                                for record in task_search:
                                    vals={
                                        'user_ids':record.user_ids.ids,
                                        'email_id':1,
                                        'name':record.name,
                                        'date_deadline':record.date_deadline
                                        }
                                    if record.project_id:
                                        vals.update({'project_id':record.project_id.name})
                                    line_list.append(vals)
                                user_wise_overdue_task.update({
                                    user.id:line_list
                                    })
                    if user_wise_overdue_task:
                        for key in user_wise_overdue_task.keys():
                            notify = self.env['sh.project.task.overdue.notify'].search([])
                            if notify:
                                notify.unlink()
                            user_email_search = self.env['sh.project.task.overdue.email'].search([])
                            if user_email_search:
                                user_email_search.user_ids = [key]
                                user_email_search.company_id = comp_rec.id

                            for user_wise_task in user_wise_overdue_task[key]:
                                self.env['sh.project.task.overdue.notify'].create(user_wise_task)
                            template = self.env.ref('sh_all_in_one_pms.template_project_task_overdue_notify_email')
                            if template:
                                template.sudo().send_mail(1,force_send=True)
