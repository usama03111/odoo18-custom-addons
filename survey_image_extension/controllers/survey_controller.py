from odoo import http
from odoo.http import request
from odoo.addons.survey.controllers.main import Survey
import logging
import base64

_logger = logging.getLogger(__name__)


class SurveyController(Survey):

    @http.route('/survey/submit_with_files/<string:survey_token>/<string:answer_token>',
                type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def survey_submit_with_files(self, survey_token, answer_token, **post):
        """Handle file uploads for survey submissions"""
        _logger.info("Custom survey submit with files called")
        _logger.info(f"POST data keys: {list(post.keys())}")

        try:
            # Check if there are files in the request
            files = request.httprequest.files
            _logger.info(f"Files in request: {list(files.keys())}")

            # Process attachment questions (handle multiple files)
            attachment_questions = {}
            for key, file_obj in files.items():
                if key.startswith('attachment_'):
                    # Handle both single files (attachment_X) and multiple files (attachment_X_Y)
                    if '_' in key.replace('attachment_', ''):
                        # Multiple file format: attachment_X_Y
                        parts = key.split('_')
                        if len(parts) >= 3 and parts[-1].isdigit():
                            question_id = '_'.join(parts[1:-1])  # Get question ID
                            file_index = int(parts[-1])  # Get file index
                        else:
                            continue
                    else:
                        # Single file format: attachment_X
                        question_id = key.replace('attachment_', '')
                        file_index = 0

                    # Read the file content and store as binary data
                    file_content = file_obj.read()
                    file_obj.seek(0)  # Reset file pointer for potential future use

                    # Initialize question data if not exists
                    if question_id not in attachment_questions:
                        attachment_questions[question_id] = {
                            'files': [],  # List to store multiple files
                            'text': post.get(question_id, '')
                        }

                    # Add file data to the list
                    attachment_questions[question_id]['files'].append({
                        'file_content_base64': base64.b64encode(file_content).decode('utf-8'),
                        'filename': file_obj.filename,
                        'index': file_index
                    })

                    _logger.info(f"Found attachment file {file_index} for question {question_id}: file={file_obj.filename}, size={len(file_content)} bytes")

            # Store attachment data in session for later processing
            if attachment_questions:
                request.session['survey_attachments'] = attachment_questions
                _logger.info(f"Stored {len(attachment_questions)} attachment questions in session")

                # Also store in a global variable for immediate access
                import threading
                if not hasattr(threading.current_thread(), 'survey_attachments'):
                    threading.current_thread().survey_attachments = {}
                threading.current_thread().survey_attachments.update(attachment_questions)
                _logger.info(f"Stored {len(attachment_questions)} attachment questions in thread local storage")

            # Convert form data to JSON format for the original method
            json_data = {}
            for key, value in post.items():
                if not key.startswith('attachment_'):
                    # Check for JSON_DATA prefix (used for complex structures like matrix)
                    if isinstance(value, str) and value.startswith('JSON_DATA:'):
                        try:
                            import json
                            json_data[key] = json.loads(value[10:])  # Strip 'JSON_DATA:' prefix
                        except Exception as e:
                            _logger.error(f"Failed to parse JSON data for key {key}: {e}")
                            json_data[key] = value
                    else:
                        json_data[key] = value

            # Add the text values from attachment questions to json_data
            for question_id, data in attachment_questions.items():
                if data.get('text'):
                    json_data[question_id] = data['text']

            _logger.info(f"Calling JSON method with data: {json_data}")

            # Call the original JSON method
            result = self.survey_submit(survey_token, answer_token, **json_data)

            # Clear attachment data from session after successful submission
            if 'survey_attachments' in request.session:
                _logger.info("Clearing attachment data from session after submission")
                del request.session['survey_attachments']

            # Also clear thread local storage
            import threading
            if hasattr(threading.current_thread(), 'survey_attachments'):
                _logger.info("Clearing attachment data from thread local storage after submission")
                delattr(threading.current_thread(), 'survey_attachments')

            # Return JSON response
            return request.make_json_response(result)

        except Exception as e:
            _logger.error(f"Error in survey submission: {e}")
            return request.make_json_response({'error': str(e)})

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>',
                type='json', auth='public', website=True)
    def survey_submit(self, survey_token, answer_token, **post):
        """Override JSON survey submit to handle file uploads from session"""
        _logger.info("Custom JSON survey submit called")
        _logger.info(f"POST data keys: {list(post.keys())}")

        # Check if there are attachment questions in session from previous requests
        if 'survey_attachments' in request.session:
            _logger.info("Found attachment data in session")
            # The attachment data is already processed and stored in session
            # The model will pick it up from there

        # Call the parent method
        result = super().survey_submit(survey_token, answer_token, **post)

        # Clear any leftover attachment data from session after processing
        if 'survey_attachments' in request.session:
            _logger.info("Clearing leftover attachment data from session after JSON submission")
            del request.session['survey_attachments']

        # Also clear thread local storage
        import threading
        if hasattr(threading.current_thread(), 'survey_attachments'):
            _logger.info("Clearing leftover attachment data from thread local storage after JSON submission")
            delattr(threading.current_thread(), 'survey_attachments')

        return result
