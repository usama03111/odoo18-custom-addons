# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    approval_config_id = fields.Many2one(
        'sh.task.approval.config', string="Task Approval Level", compute="_compute_approval_level", store=True)
    user_ids = fields.Many2many('res.users', string="Approval Users")
    level = fields.Integer(string="Next Approval Level")
    group_ids = fields.Many2many('res.groups', string="Approval Groups")
    approval_info_line = fields.One2many(
        'sh.task.approval.info', 'sh_task_id')
    rejection_date = fields.Datetime(string="Reject Date")
    reject_by = fields.Many2one('res.users', string="Reject By")
    reject_reason = fields.Char(string="Reject Reason")
    is_approval_user = fields.Boolean(
        'Is Approval User', compute="_compute_is_approval_user", search="_search_is_approval_user")
    requires_approval = fields.Boolean(compute="_compute_requires_approval", store=True)
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Approval Status", default='draft')

    @api.depends('project_id', 'stage_id')
    def _compute_approval_level(self):
        for task in self:
            task.approval_config_id = self.env['sh.task.approval.config'].search([
                '|', ('project_ids', '=', False), ('project_ids', 'in', task.project_id.ids),
                '|', ('stage_ids', '=', False), ('stage_ids', 'in', task.stage_id.ids),
                ('company_ids', 'in', [task.company_id.id])
            ], limit=1)

    @api.depends('approval_config_id')
    def _compute_requires_approval(self):
        for task in self:
            task.requires_approval = bool(task.approval_config_id)

    def _compute_is_approval_user(self):
        for task in self:
            task.is_approval_user = False
            if self.env.user in task.user_ids or any(group in self.env.user.groups_id for group in task.group_ids):
                task.is_approval_user = True

    def _search_is_approval_user(self, operator, value):
        tasks = self.search([])
        task_ids = []
        for task in tasks:
            if self.env.user in task.user_ids or any(group in self.env.user.groups_id for group in task.group_ids):
                task_ids.append(task.id)
        return [('id', 'in', task_ids)]

    def action_submit_for_approval(self):
        self.ensure_one()
        if not self.approval_config_id or not self.approval_config_id.task_approval_line:
            raise UserError(_("No approval configuration found for this task."))

        self.approval_state = 'waiting'
        self.approval_info_line = False
        lines = self.approval_config_id.task_approval_line

        # Create approval info lines
        for line in lines:
            self.env['sh.task.approval.info'].create({
                'sh_task_id': self.id,
                'level': line.level,
                'user_ids': [(6, 0, line.user_ids.ids)],
                'group_ids': [(6, 0, line.group_ids.ids)],
            })

        # Set up first approval level
        first_line = lines[0]
        self.level = first_line.level
        if first_line.approve_by == 'group':
            self.group_ids = first_line.group_ids
            self.user_ids = False
            users = first_line.group_ids.users
        else:
            self.group_ids = False
            self.user_ids = first_line.user_ids
            users = first_line.user_ids

        # Send notifications
        template = self.env.ref('sh_task_dynamic_approval.email_template_task_approval')
        for user in users:
            template.send_mail(self.id, force_send=True, email_values={
                'email_to': user.email,
                'email_from': self.env.user.email
            })
            self.env['bus.bus']._sendone(
                user.partner_id,
                'sh_notification_info',
                {
                    'title': _('Task Approval Notification'),
                    'message': f'Task {self.name} requires your approval'
                }
            )


    def action_approve(self):
        self.ensure_one()

        if not self.is_approval_user:
            raise UserError(_("You don't have permission to approve this task."))

        # Mark current level as approved
        info_line = self.approval_info_line.filtered(lambda x: x.level == self.level)
        if info_line:
            info_line.write({
                'status': True,
                'approval_date': fields.Datetime.now(),
                'approved_by': self.env.user.id,
            })

        curr_line = self.approval_config_id.task_approval_line.filtered(lambda x: x.level == self.level)
        next_line = self.approval_config_id.task_approval_line.filtered(lambda x: x.level > self.level)

        if next_line:
            next_line = next_line[0]
            self.level = next_line.level

            # Set next level approvers
            if next_line.approve_by == 'group':
                self.group_ids = next_line.group_ids
                self.user_ids = False
                users = next_line.group_ids.users
            else:
                self.group_ids = False
                self.user_ids = next_line.user_ids
                users = next_line.user_ids

            # Notify next level users
            template = self.env.ref('sh_task_dynamic_approval.email_template_task_approval')
            for user in users:
                template.send_mail(self.id, force_send=True, email_values={
                    'email_to': user.email,
                    'email_from': self.env.user.email
                })
                self.env['bus.bus']._sendone(
                    user.partner_id,
                    'sh_notification_info',
                    {
                        'title': _('Task Approval Notification'),
                        'message': f'Task {self.name} requires your approval'
                    }
                )
        else:
            # Final approval
            self.write({
                'approval_state': 'approved',
                'level': 0,
                'group_ids': False,
                'user_ids': False,
            })

            # Notify all assigned users
            if self.user_ids:
                template = self.env.ref('sh_task_dynamic_approval.email_template_task_approved')
                for user in self.user_ids:
                    template.send_mail(self.id, force_send=True, email_values={
                        'email_to': user.email,
                        'email_from': self.env.user.email
                    })
                    self.env['bus.bus']._sendone(
                        user.partner_id,
                        'sh_notification_info',
                        {
                            'title': _('Task Approved'),
                            'message': f'Your task {self.name} has been approved'
                        }
                    )

    def action_reject(self):
        return {
            'name': _('Reject Task'),
            'type': 'ir.actions.act_window',
            'res_model': 'sh.task.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_id': self.id}
        } 