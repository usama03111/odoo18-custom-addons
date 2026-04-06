# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields

class ProjectMileStone(models.Model):
    _inherit = 'project.milestone'

    state = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
                             string="State", default='new', readonly=True, index=True)

    def button_inprogress(self):
        if self:
            for data in self:
                data.write({'state': 'in_progress'})

    def button_completed(self):
        if self:
            for data in self:
                data.write({'state': 'completed'})

    def button_cancelled(self):
        if self:
            for data in self:
                data.write({'state': 'cancelled'})

    def sh_action_milestone_to_task_event(self):
        self.ensure_one()
        return{
            'name':'Milestone To Task',
            'type':'ir.actions.act_window',
            'res_model':'project.task',
            'view_mode':'kanban,tree,form',
            'domain':[('milestone_ids','in',[self.id])],
            'context':{'default_milestone_ids':[(6,0,[self.id])]},
            'target':'current',
        }
