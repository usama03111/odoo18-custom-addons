# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, api

class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def create(self,vals):   
        res = super().create(vals)
        if res.stage_id and res.stage_id.assign_to:
            res.user_ids = [(4,res.stage_id.assign_to.id)]
        return res

    def write(self,vals):
        if self:
            if vals.get('stage_id'):
                stage = self.env["project.task.type"].browse(vals['stage_id'])
                if stage and stage.assign_to:
                    vals['user_ids'] = [(4,stage.assign_to.id)]
        return super().write(vals)
