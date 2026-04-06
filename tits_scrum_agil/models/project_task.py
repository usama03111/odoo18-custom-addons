from odoo import models, fields, api, _


class ScrumSprint(models.Model):
    _inherit = "project.task"
    _order = "sequence"

    user_id = fields.Many2one('res.users', 'Assigned to', select=True, track_visibility='onchange')
    actor_ids = fields.Many2many(comodel_name='project.scrum.actors', string='Actor')
    us_id = fields.Many2one(comodel_name='project.scrum.us', string='User Stories')
    use_scrum = fields.Boolean(related='project_id.use_scrum')
    sprint_id = fields.Many2one(comodel_name='project.scrum.sprint', string='Sprint', related='us_id.sprint_id')
    description = fields.Html('Description')
