from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero
from odoo.http import request

class SurveyUserInputLine(models.Model):
    _name = "survey.user_input.line"
    _inherit = ['survey.user_input.line', 'mail.thread', 'mail.activity.mixin']

    answer_type = fields.Selection(
        selection_add=[('attachment', 'Attachment')],
        ondelete={'attachment': 'set null'}
    )
    
    value_attachment = fields.Binary('Attachment answer', help='For attachment type answers')

    @api.depends(
        'answer_type', 'value_text_box', 'value_numerical_box',
        'value_char_box', 'value_date', 'value_datetime',
        'suggested_answer_id.value', 'matrix_row_id.value',
    )
    def _compute_display_name(self):
        """Extend display name computation to include attachment type without disturbing default logic."""
        super(SurveyUserInputLine, self)._compute_display_name()

        for line in self:
            if line.answer_type == 'attachment':
                # Only override if display_name wasn't set by default logic
                attachments = self.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'survey.user_input.line'),
                    ('res_id', '=', line.id)
                ])
                if attachments:
                    count = len(attachments)
                    line.display_name = f"{count} file(s) attached"
                else:
                    line.display_name = _("Skipped")


    # def _get_answer_matching_domain(self):
    #     """Extend to handle attachment type"""
    #     result = super()._get_answer_matching_domain()
    #     if self.answer_type == 'attachment':
    #         # For attachments, match by question only
    #         return ['&', ('question_id', '=', self.question_id.id), ('answer_type', '=', 'attachment')]
    #     return result
    #
    # @api.model
    # def _get_answer_score_values(self, vals, compute_speed_score=True):
    #     """Override to handle attachment type (not scored)"""
    #     result = super()._get_answer_score_values(vals, compute_speed_score)
    #     if vals.get('answer_type') == 'attachment':
    #         # Attachments are not scored
    #         result.update({'answer_is_correct': False, 'answer_score': 0})
    #     return result

    def action_open_popup_form(self):
        """these methode show the form view of a answer"""
        self.ensure_one()

        # separate view ID (for popup)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input.line',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',  # Popup
            'flags': {
                'form': {
                    'action_buttons': True,
                    'options': {'mode': 'edit'}
                }
            },
            'context': self.env.context,
        }
