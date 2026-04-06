from odoo import models, fields, api

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        """Extend to handle attachment type questions"""
        # Handle attachment question type before calling super()
        if question.question_type == 'attachment':
            import logging, base64, json, threading
            _logger = logging.getLogger(__name__)
            
            # Remove previous lines if needed
            existing_lines = self.user_input_line_ids.filtered(lambda l: l.question_id == question)
            if overwrite_existing and existing_lines:
                existing_lines.unlink()

            text_value = str(answer) if answer else ''
            image_data = None
            filename = None
            
            # Try to get attachment data from thread local storage first, then session
            try:
                thread_attachments = getattr(threading.current_thread(), 'survey_attachments', {})
                
                if thread_attachments:
                    question_data = thread_attachments.get(str(question.id))
                    
                    if question_data:
                        # Get text from the attachment data
                        if 'text' in question_data:
                            text_value = question_data['text']
                        
                        # Get file data (handle both single and multiple files)
                        if 'files' in question_data and question_data['files']:
                            # Create a combined data structure
                            combined_files = []
                            for file_info in question_data['files']:
                                combined_files.append({
                                    'filename': file_info['filename'],
                                    'content': file_info['file_content_base64']
                                })
                            
                            # Store as JSON string in base64 format
                            files_json = json.dumps(combined_files)
                            image_data = base64.b64encode(files_json.encode('utf-8')).decode('utf-8')
                            filename = f"{len(combined_files)}_files.json"
                        else:
                            # Single file (backward compatibility)
                            file_content_base64 = question_data.get('file_content_base64')
                            filename = question_data.get('filename')
                            if file_content_base64:
                                # Store the base64 data directly (don't decode it)
                                image_data = file_content_base64
                            
                        # Clean up thread data for this question
                        if str(question.id) in thread_attachments:
                            del thread_attachments[str(question.id)]
                            # If no more attachments, clear the entire thread storage
                            if not thread_attachments:
                                delattr(threading.current_thread(), 'survey_attachments')
                else:
                    # Fallback to session if thread storage is empty
                    request = self.env.context.get('request')
                    
                    if request and hasattr(request, 'session') and 'survey_attachments' in request.session:
                        attachments = request.session.get('survey_attachments', {})
                        question_data = attachments.get(str(question.id))
                        
                        if question_data:
                            # Get text from the attachment data
                            if 'text' in question_data:
                                text_value = question_data['text']
                            
                            # Get file data (handle both single and multiple files)
                            if 'files' in question_data and question_data['files']:
                                # Create a combined data structure
                                combined_files = []
                                for file_info in question_data['files']:
                                    combined_files.append({
                                        'filename': file_info['filename'],
                                        'content': file_info['file_content_base64']
                                    })
                                
                                # Store as JSON string in base64 format
                                files_json = json.dumps(combined_files)
                                image_data = base64.b64encode(files_json.encode('utf-8')).decode('utf-8')
                                filename = f"{len(combined_files)}_files.json"
                            else:
                                # Single file (backward compatibility)
                                file_content_base64 = question_data.get('file_content_base64')
                                filename = question_data.get('filename')
                                if file_content_base64:
                                    # Store the base64 data directly (don't decode it)
                                    image_data = file_content_base64
                                
                            # Clean up session data for this question
                            if str(question.id) in request.session.get('survey_attachments', {}):
                                del request.session['survey_attachments'][str(question.id)]
                                if not request.session['survey_attachments']:
                                    del request.session['survey_attachments']
                        else:
                            _logger.warning(f"No attachment data found for question {question.id} in session")
                    else:
                        _logger.warning("No request, session, or thread storage available")
            except Exception as e:
                _logger.warning(f"Could not access attachment data: {e}")

            # If there's no text value and no file, mark as skipped
            if not text_value and not image_data:
                try:
                    self.env['survey.user_input.line'].create({
                        'user_input_id': self.id,
                        'question_id': question.id,
                        'skipped': True,
                        'answer_type': None,
                    })
                except Exception as e:
                    _logger.error(f"Error creating skipped line: {e}")
                    raise
            else:
                # If we have a file but no text, provide a default text to satisfy validation
                if image_data and not text_value:
                    text_value = f"File attached: {filename}" if filename else "File attached"
                
                # Store all files in ONE answer line
                try:
                    # Create the answer line first
                    answer_line = self.env['survey.user_input.line'].create({
                        'user_input_id': self.id,
                        'question_id': question.id,
                        'answer_type': 'attachment',
                        'value_text_box': text_value,
                        'value_attachment': base64.b64encode(b'placeholder').decode('utf-8'),  # Base64 encode the placeholder
                        'skipped': False,
                    })
                    
                    # Normalize into a list of files, then create attachments
                    files_data = []
                    if image_data and filename and filename.endswith('_files.json'):
                        # Multiple files - decode the JSON data
                        try:
                            # Fix padding for base64 then decode JSON
                            padded = image_data + '=' * (-len(image_data) % 4)
                            files_json = base64.b64decode(padded).decode('utf-8')
                            files_data = json.loads(files_json) or []
                        except Exception as e:
                            _logger.error(f"Error decoding multiple files JSON: {e}")
                            files_data = []
                    elif image_data:
                        # Single file - wrap into a list
                        files_data = [{
                            'filename': filename or 'file',
                            'content': image_data,
                        }]

                    _logger.info(f"Creating {len(files_data)} attachments for answer line {answer_line.id}")
                    for file_info in files_data:
                        file_content_base64 = file_info.get('content', '')
                        file_filename = file_info.get('filename', 'file')

                        # Ensure non-empty and fix padding if needed (Odoo expects base64 string in datas)
                        if not file_content_base64:
                            _logger.warning(f"Skipping file {file_filename} - no content")
                            continue
                        file_content = file_content_base64 + '=' * (-len(file_content_base64) % 4)

                        # Determine mimetype based on extension
                        mimetype = 'application/octet-stream'
                        if file_filename.lower().endswith('.pdf'):
                            mimetype = 'application/pdf'
                        elif file_filename.lower().endswith(('.jpg', '.jpeg')):
                            mimetype = 'image/jpeg'
                        elif file_filename.lower().endswith('.png'):
                            mimetype = 'image/png'
                        elif file_filename.lower().endswith(('.xlsx', '.xls')):
                            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                        # Create attachment
                        try:
                            self.env['ir.attachment'].sudo().create({
                                'name': file_filename,
                                'type': 'binary',
                                'datas': file_content,
                                'mimetype': mimetype,
                                'res_model': 'survey.user_input.line',
                                'res_id': answer_line.id,
                            })
                            _logger.info(f"Successfully created attachment: {file_filename}")
                        except Exception as e:
                            _logger.error(f"Error creating attachment {file_filename}: {e}")
                    if files_data:
                        _logger.info(f"Created {len(files_data)} attachments")
                        
                except Exception as e:
                    _logger.error(f"Error creating answer line: {e}")
                    raise
            return self  # Return early for attachment type

        # For all other question types, call the parent method
        return super()._save_lines(question, answer, comment, overwrite_existing)