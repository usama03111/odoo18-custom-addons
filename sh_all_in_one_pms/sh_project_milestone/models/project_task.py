# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields,api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    milestone_ids = fields.Many2many('project.milestone', string="Milestone ")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('project_id'):
                project = self.env['project.project'].sudo().browse(vals.get('project_id'))
                if project and project.milestone_ids:
                    vals.update({
                        'milestone_ids':[(6,0,project.milestone_ids.ids)]
                    })
        return super(ProjectTask,self).create(vals_list)

    def write(self,vals):
        if vals.get('project_id'):
            project = self.env['project.project'].sudo().browse(vals.get('project_id'))
            if project and project.milestone_ids:
                vals.update({
                    'milestone_ids':[(6,0,project.milestone_ids.ids)]
                })
        return super(ProjectTask,self).write(vals)
