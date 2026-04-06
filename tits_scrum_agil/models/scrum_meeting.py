from odoo import models, fields, api, _
from datetime import date, timedelta


class ScrumMeeting(models.Model):
    _name = 'project.scrum.meeting'
    _description = 'Project Scrum Daily Meetings'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one(comodel_name='project.project', string='Project', ondelete='set null', track_visibility='onchange', change_default=True)
    name = fields.Char(string='Meeting', compute='_compute_meeting_name', size=60)
    sprint_id = fields.Many2one(comodel_name='project.scrum.sprint', string='Sprint')
    date_meeting = fields.Date(string='Date', required=True, default=date.today())
    user_id_meeting = fields.Many2one(comodel_name='res.users', string='Name', required=True,
                                      default=lambda self: self.env.user)
    question_yesterday = fields.Text(string='Description', required=True)
    question_today = fields.Text(string='Description', required=True)
    question_blocks = fields.Text(string='Description', required=False)
    question_backlog = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Backlog Accurate?', required=False,
                                        default='yes')

    def _compute_meeting_name(self):
        #get name
        if self.project_id:
            self.name = "%s - %s - %s" % (self.project_id.name, self.user_id_meeting.name, self.date_meeting)
        else:
            self.name = "%s - %s" % (self.user_id_meeting.name, self.date_meeting)

    def send_email(self):
        #send email
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        template = self.env.ref('tits_scrum_agil.email_template_id', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='project.scrum.meeting',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template,
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
