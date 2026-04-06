from odoo import models, fields, api, _


class ScrumCase(models.Model):
    _name = 'project.scrum.test'
    _description = 'Scrum Case'
    _order = 'sequence_test'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer('Color Index')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', ondelete='set null',
                                 track_visibility='onchange', change_default=True)
    sprint_id = fields.Many2one(comodel_name='project.scrum.sprint', string='Sprint')
    user_story_id_test = fields.Many2one(comodel_name="project.scrum.us", string="User Story")
    description_test = fields.Html(string='Description')
    sequence_test = fields.Integer(string='Sequence', select=True)
    stats_test = fields.Selection([('draft', 'Draft'), ('in progress', 'In Progress'), ('cancel', 'Cancelled')],
                                  string='State')
