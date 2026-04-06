from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero
from odoo.http import request


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    question_type = fields.Selection(
        selection_add=[('attachment', 'Attachment Upload')],
        ondelete={'attachment': 'set null'}
    )

    def validate_question(self, answer, comment=None):
        self.ensure_one()
        if self.question_type != 'attachment':
            return super().validate_question(answer, comment)

        # Attachment: check thread/session for presence
        files_present = False
        try:
            import threading
            thread_attachments = getattr(threading.current_thread(), 'survey_attachments', {})
            qdata = thread_attachments.get(str(self.id)) or {}
            files_present = bool(qdata.get('files'))
            if not files_present:
                # Fallback to HTTP session directly
                if request and hasattr(request, 'session'):
                    sess = request.session or {}
                    qdata = (sess.get('survey_attachments') or {}).get(str(self.id)) or {}
                    files_present = bool(qdata.get('files'))
        except Exception:
            files_present = False

        if self.constr_mandatory and not files_present:
            return {self.id: self.constr_error_msg or _('This question requires an answer')}
        return {}
