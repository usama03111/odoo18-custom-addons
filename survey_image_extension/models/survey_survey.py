from odoo import models, fields, api, _


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def _get_survey_questions(self, answer=None, page_id=None, question_id=None):
        """Ensure mandatory attachment questions block the page until files are present.
        If layout is page_per_section and current section has mandatory attachment
        questions without files, only return those questions so core validation
        shows the error and prevents saving other answers on the page.
        """
        res_questions, res_id = super()._get_survey_questions(answer=answer, page_id=page_id, question_id=question_id)

        # Only apply on section layout with a current page and an existing answer
        if self.questions_layout != 'page_per_section' or not answer or not page_id:
            return res_questions, res_id

        # Filter to the current section's questions (super already did, but be safe)
        section_questions = res_questions
        if not section_questions:
            return res_questions, res_id

        # Find mandatory attachment questions in this section
        mandatory_attach = section_questions.filtered(lambda q: q.question_type == 'attachment' and q.constr_mandatory)
        if not mandatory_attach:
            return res_questions, res_id

        # Check files presence per question using thread/session (same logic as validate_question)
        import threading
        missing_files_questions = self.env['survey.question']
        try:
            thread_attachments = getattr(threading.current_thread(), 'survey_attachments', {})
        except Exception:
            thread_attachments = {}

        request = self.env.context.get('request')
        session_map = request.session.get('survey_attachments', {}) if request and hasattr(request, 'session') else {}

        for q in mandatory_attach:
            qid = str(q.id)
            qdata = thread_attachments.get(qid) or session_map.get(qid) or {}
            files_present = bool(qdata.get('files'))
            if not files_present:
                missing_files_questions |= q

        # If any mandatory attachment is missing files, only validate those
        if missing_files_questions:
            return missing_files_questions, res_id

        return res_questions, res_id