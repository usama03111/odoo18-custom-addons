from odoo import http
from odoo.http import request
import json
import logging
import re
import traceback
import sys
_logger = logging.getLogger(__name__)

class WhatsAppWebhookController(http.Controller):

    @http.route('/whatsapp/webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def webhook(self, **kwargs):
        """Handle WhatsApp webhook from Meta"""
        
        try:
            _logger.info(f"=== WHATSAPP WEBHOOK RECEIVED ===")
            _logger.info(f"Method: {request.httprequest.method}")
            _logger.info(f"Headers: {dict(request.httprequest.headers)}")
            _logger.info(f"Query params: {kwargs}")
            
            # Handle GET request (webhook verification)
            if request.httprequest.method == 'GET':
                _logger.info("Processing webhook verification request")
                return self.handle_webhook_verification(kwargs)
            
            # Handle POST request (incoming messages)
            elif request.httprequest.method == 'POST':
                _logger.info("Processing incoming message request")
                _logger.info(f"Raw data length: {len(request.httprequest.data) if request.httprequest.data else 0}")
                return self.handle_incoming_message(request.httprequest.data)
            else:
                _logger.warning(f"Unsupported HTTP method: {request.httprequest.method}")
                return "Method not allowed"
                
        except Exception as e:
            _logger.error(f"=== WEBHOOK CRITICAL ERROR ===")
            _logger.error(f"Error type: {type(e).__name__}")
            _logger.error(f"Error message: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Request method: {request.httprequest.method}")
            _logger.error(f"Request data: {request.httprequest.data}")
            _logger.error(f"Request kwargs: {kwargs}")
            return "Error"
    
    def handle_webhook_verification(self, params):
        """Handle webhook verification from Meta"""
        try:
            _logger.info("=== WEBHOOK VERIFICATION START ===")
            _logger.info(f"Received params: {params}")
            
            # Meta sends these parameters for verification
            mode = params.get('hub.mode')
            token = params.get('hub.verify_token')
            challenge = params.get('hub.challenge')
            
            _logger.info(f"Verification params - mode: {mode}, token: {token[:10]}..., challenge: {challenge}")
            
            _logger.info(f"Verification params - mode: {mode}, token: {token[:10] if token else ''}..., challenge: {challenge}")
            
            # Find account with matching verify token
            matching_account = request.env['whatsapp.account'].sudo().search([
                ('webhook_verify_token', '=', token)
            ], limit=1)
            
            if not matching_account:
                _logger.warning("No WhatsApp account found with this verify token")
                return "Forbidden"
            
            if mode == 'subscribe':
                _logger.info(f"Webhook verification successful for account: {matching_account.name}")
                resp = request.make_response(challenge)
                resp.headers['Content-Type'] = 'text/plain'
                return resp
            else:
                _logger.warning(f"Webhook verification failed - mode: {mode}")
                return "Forbidden"
                
        except Exception as e:
            _logger.error(f"=== WEBHOOK VERIFICATION ERROR ===")
            _logger.error(f"Error type: {type(e).__name__}")
            _logger.error(f"Error message: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Params received: {params}")
            return "Error"
    
    def handle_incoming_message(self, data):
        """Handle incoming WhatsApp messages"""
        try:
            _logger.info("=== INCOMING MESSAGE PROCESSING START ===")
            _logger.info(f"Raw data type: {type(data)}")
            _logger.info(f"Raw data length: {len(data) if data else 0}")
            
            if not data:
                _logger.warning("No data received in webhook")
                return "No data"
            
            # Parse the webhook data
            try:
                _logger.info("Attempting to parse JSON data")
                webhook_data = json.loads(data)
                _logger.info(f"JSON parsed successfully. Keys: {list(webhook_data.keys())}")
            except json.JSONDecodeError as e:
                _logger.error(f"=== JSON PARSING ERROR ===")
                _logger.error(f"JSON parsing failed: {str(e)}")
                _logger.error(f"Raw data: {data}")
                return "Invalid JSON"
            
            # Process messages
            if 'entry' in webhook_data and webhook_data['entry']:
                _logger.info(f"Found {len(webhook_data['entry'])} entries in webhook data")
                for entry_idx, entry in enumerate(webhook_data['entry']):
                    _logger.info(f"Processing entry {entry_idx}: {list(entry.keys())}")
                    if 'changes' in entry and entry['changes']:
                        _logger.info(f"Found {len(entry['changes'])} changes in entry")
                        for change_idx, change in enumerate(entry['changes']):
                            _logger.info(f"Processing change {change_idx}: {list(change.keys())}")
                            if change.get('value') and 'messages' in change['value']:
                                messages = change['value']['messages']
                                _logger.info(f"Found {len(messages)} messages to process")
                                for msg_idx, message in enumerate(messages):
                                    _logger.info(f"Processing message {msg_idx}: {list(message.keys())}")
                                    try:
                                        self.process_message(message)
                                        _logger.info(f"Message {msg_idx} processed successfully")
                                    except Exception as msg_error:
                                        _logger.error(f"=== MESSAGE PROCESSING ERROR ===")
                                        _logger.error(f"Error processing message {msg_idx}: {str(msg_error)}")
                                        _logger.error(f"Message data: {message}")
                                        _logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                _logger.warning("No entries found in webhook data or entries is empty")
                _logger.info(f"Webhook data structure: {webhook_data}")
            
            _logger.info("=== INCOMING MESSAGE PROCESSING COMPLETED ===")
            return "OK"
            
        except Exception as e:
            _logger.error(f"=== INCOMING MESSAGE CRITICAL ERROR ===")
            _logger.error(f"Error type: {type(e).__name__}")
            _logger.error(f"Error message: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Raw data: {data}")
            return "Error"
    
    def process_message(self, message):
        """Process individual WhatsApp message"""
        try:
            _logger.info("=== PROCESSING INDIVIDUAL MESSAGE ===")
            _logger.info(f"Message structure: {list(message.keys())}")
            
            # Extract message details
            from_number = message.get('from', '')
            message_type = message.get('type', '')
            timestamp = message.get('timestamp', '')
            message_id = message.get('id', '')
            
            _logger.info(f"Message details - from: {from_number}, type: {message_type}, timestamp: {timestamp}, id: {message_id}")
            
            # Get message content based on type
            if message_type == 'text':
                message_text = message.get('text', {}).get('body', '')
                _logger.info(f"Text message content: {message_text[:100]}...")
            elif message_type == 'image':
                image_data = message.get('image', {})
                message_text = f"[Image received] - {image_data.get('id', '')}"
                _logger.info(f"Image message - ID: {image_data.get('id')}, caption: {image_data.get('caption', 'N/A')}")
            elif message_type == 'document':
                doc_data = message.get('document', {})
                message_text = f"[Document received] - {doc_data.get('filename', '')}"
                _logger.info(f"Document message - filename: {doc_data.get('filename')}, ID: {doc_data.get('id')}")
            elif message_type == 'audio':
                audio_data = message.get('audio', {})
                message_text = f"[Audio message received] - {audio_data.get('id', '')}"
                _logger.info(f"Audio message - ID: {audio_data.get('id')}, voice: {audio_data.get('voice', False)}")
            elif message_type == 'video':
                video_data = message.get('video', {})
                message_text = f"[Video message received] - {video_data.get('id', '')}"
                _logger.info(f"Video message - ID: {video_data.get('id')}, caption: {video_data.get('caption', 'N/A')}")
            elif message_type == 'location':
                location = message.get('location', {})
                message_text = f"[Location received] - Lat: {location.get('latitude', 'N/A')}, Long: {location.get('longitude', 'N/A')}"
                _logger.info(f"Location message - lat: {location.get('latitude')}, long: {location.get('longitude')}")
            else:
                message_text = f"[{message_type.title()} message received]"
                _logger.info(f"Unknown message type: {message_type}")
            
            # Check for context/reply information
            context_id = None
            try:
                context_id = (message.get('context') or {}).get('id')
                if context_id:
                    _logger.info(f"Message is a reply to context_id: {context_id}")
                else:
                    _logger.info("Message is not a reply (no context)")
            except Exception as e:
                _logger.warning(f"Error extracting context: {str(e)}")
                context_id = None
            
            # Resolve target record from WhatsApp reply context across ANY model
            _logger.info("Attempting to resolve target record...")
            target_record = self.resolve_record_for_incoming(message)
            
            if target_record:
                _logger.info(f"Target record found: {target_record._name} (ID: {target_record.id})")
                # Log message on the resolved record chatter
                try:
                    self.log_message_on_record(target_record, from_number, message_text, timestamp, message_type, message_id, context_id)
                    _logger.info("Message logged to target record successfully")
                except Exception as e:
                    _logger.error(f"Error logging to target record: {str(e)}")
                    _logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                _logger.info("No target record found, processing as standalone message")
                # No target record found - find or create partner and log to Discuss channel
                try:
                    _logger.info("Searching for existing partner...")
                    # First try to find existing partner
                    partner = self.find_partner_by_phone(from_number)
                    
                    if partner:
                        _logger.info(f"Found existing partner: {partner.name} (ID: {partner.id})")
                    else:
                        _logger.info("No existing partner found, creating new one...")
                        # If no partner found, create a new one
                        partner = self.create_partner_from_whatsapp(from_number, message_text, message_type)
                        if partner:
                            _logger.info(f"Created new partner from WhatsApp: {partner.name} (ID: {partner.id})")
                        else:
                            _logger.error("Failed to create new partner")
                    
                    if partner:
                        body_text = message_text if message_type == 'text' else f"WhatsApp {message_type.title()}: {message_text}"
                        if message_id:
                            fingerprint = f"wa:{message_id}"
                        else:
                            clean = re.sub(r'\D', '', str(from_number or ''))
                            fingerprint = f"wa:{clean}:{timestamp}"
                        
                        _logger.info(f"Logging to Discuss channel with fingerprint: {fingerprint}")
                        
                        # Log to Discuss channel (will create channel if needed)
                        try:
                            result = request.env['whatsapp.logger'].log_incoming_if_exists(
                                partner, 
                                body_text, 
                                fingerprint, 
                                context_id=context_id
                            )
                            if result:
                                _logger.info("Message logged to Discuss channel successfully")
                            else:
                                _logger.warning("Failed to log message to Discuss channel")
                        except Exception as e:
                            _logger.error(f"Error logging to Discuss channel: {str(e)}")
                            _logger.error(f"Traceback: {traceback.format_exc()}")
                    else:
                        _logger.warning(f"Could not find or create partner for WhatsApp number: {from_number}")
                        
                except Exception as e:
                    _logger.error(f"=== PARTNER HANDLING ERROR ===")
                    _logger.error(f"Partner handling failed: {str(e)}")
                    _logger.error(f"Traceback: {traceback.format_exc()}")
                    _logger.error(f"From number: {from_number}")
                    _logger.error(f"Message text: {message_text}")
                
        except Exception as e:
            _logger.error(f"=== MESSAGE PROCESSING CRITICAL ERROR ===")
            _logger.error(f"Error type: {type(e).__name__}")
            _logger.error(f"Error message: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Message data: {message}")

    def create_partner_from_whatsapp(self, phone_number, message_text, message_type):
        """Create a new partner from WhatsApp contact information"""
        try:
            _logger.info(f"=== CREATING PARTNER FROM WHATSAPP ===")
            _logger.info(f"Phone number: {phone_number}")
            _logger.info(f"Message text: {message_text[:100]}...")
            _logger.info(f"Message type: {message_type}")
            
            clean_phone = self.clean_phone_number(phone_number)
            _logger.info(f"Cleaned phone: {clean_phone}")
            
            if not clean_phone:
                _logger.warning(f"Invalid phone number for partner creation: {phone_number}")
                return False
            
            # Generate partner name from phone number
            # Format: +1234567890 -> WhatsApp +1 (234) 567-890
            formatted_phone = self.format_phone_for_display(clean_phone)
            partner_name = f"WhatsApp {formatted_phone}"
            
            _logger.info(f"Formatted phone: {formatted_phone}")
            _logger.info(f"Partner name: {partner_name}")
            
            # Create partner with basic information
            partner_vals = {
                'name': partner_name,
                'phone': formatted_phone,
                'mobile': formatted_phone,
                'is_company': False,
                'customer_rank': 1,  # Mark as customer
                'comment': f"Created from WhatsApp contact. First message: {message_text[:100]}{'...' if len(message_text) > 100 else ''}",
            }

            _logger.info(f"Partner values: {partner_vals}")
            partner = request.env['res.partner'].sudo().create(partner_vals)
            _logger.info(f"Created new partner: {partner.name} (ID: {partner.id}) for WhatsApp: {phone_number}")
            return partner
            
        except Exception as e:
            _logger.error(f"=== PARTNER CREATION ERROR ===")
            _logger.error(f"Error creating partner from WhatsApp: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Phone number: {phone_number}")
            _logger.error(f"Message text: {message_text}")
            _logger.error(f"Message type: {message_type}")
            return False

    def format_phone_for_display(self, phone_number):
        """Format phone number for display"""
        try:
            clean = re.sub(r'\D', '', str(phone_number))
            if len(clean) >= 10:
                if len(clean) == 10:
                    # US format: (123) 456-7890
                    return f"({clean[:3]}) {clean[3:6]}-{clean[6:]}"
                elif len(clean) == 11 and clean.startswith('1'):
                    # US format with country code: +1 (234) 567-8900
                    return f"+1 ({clean[1:4]}) {clean[4:7]}-{clean[7:]}"
                else:
                    # International format: +1234567890
                    return f"+{clean}"
            else:
                return phone_number
        except Exception:
            return phone_number

    def resolve_record_for_incoming(self, message):
        """Return a recordset (any model) based on WhatsApp reply context.
        We look up mail.message.message_id == wa:{context_id}. Prefer business records over Discuss.
        """
        try:
            _logger.info("=== RESOLVING RECORD FOR INCOMING MESSAGE ===")
            _logger.info(f"Message context: {message.get('context', {})}")
            
            context_id = None
            try:
                context_id = (message.get('context') or {}).get('id')
                _logger.info(f"Extracted context_id: {context_id}")
            except Exception as e:
                _logger.warning(f"Error extracting context_id: {str(e)}")
                context_id = None
                
            if not context_id:
                _logger.info("No context_id found, message is not a reply")
                return False
                
            _logger.info(f"Searching for mail.message with message_id: wa:{context_id}")
            MailMessage = request.env['mail.message'].sudo()
            
            # 1) Prefer a non-discuss message (original business record)
            mm = MailMessage.search([
                ('message_id', '=', f"wa:{context_id}"),
                ('model', '!=', 'discuss.channel'),
            ], limit=1, order='id desc')
            
            _logger.info(f"Found {len(mm)} matching mail messages (non-discuss)")
            
            if mm and mm.model and mm.res_id:
                _logger.info(f"Found target record: {mm.model} (ID: {mm.res_id})")
                rec = request.env[mm.model].sudo().browse(mm.res_id)
                if rec.exists():
                    _logger.info(f"Target record exists: {rec.display_name}")
                    return rec
                else:
                    _logger.warning(f"Target record does not exist: {mm.model} ID {mm.res_id}")
                    return False
            else:
                _logger.info("No matching mail message found for context_id")
                return False
                
        except Exception as e:
            _logger.error(f"=== RECORD RESOLUTION ERROR ===")
            _logger.error(f"Error resolving record from context: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Message context: {message.get('context', {})}")
            return False

    def clean_phone_number(self, phone_number):
        """Normalize WhatsApp numbers into plain string format."""
        try:
            if not phone_number:
                return ""
            
            # Remove WhatsApp prefix if present (e.g., 919876543210@s.whatsapp.net)
            if '@s.whatsapp.net' in str(phone_number):
                phone_number = str(phone_number).split('@')[0]
            
            # Remove spaces, dashes, parentheses, and other non-digits
            clean = re.sub(r'\D', '', str(phone_number))
            
            # Ensure it's a valid length (at least 10 digits)
            if len(clean) >= 10:
                return clean
            else:
                return clean
                
        except Exception as e:
            return str(phone_number) if phone_number else ""

    def log_message_on_record(self, record, from_number, message_text, timestamp, message_type, wa_message_id=None, context_id=None):
        """Post incoming WhatsApp on any record's chatter (sale.order, project.task, crm.lead, etc.)"""
        try:
            _logger.info(f"=== LOGGING MESSAGE ON RECORD ===")
            _logger.info(f"Record: {record._name} (ID: {record.id})")
            _logger.info(f"From number: {from_number}")
            _logger.info(f"Message type: {message_type}")
            _logger.info(f"Context ID: {context_id}")
            
            # Try to resolve a relevant partner
            author_partner = getattr(record, 'partner_id', False) or self.find_partner_by_phone(from_number)
            _logger.info(f"Author partner: {author_partner.name if author_partner else 'None'}")
            
            # Build fingerprint
            try:
                if wa_message_id:
                    fingerprint = f"wa:{wa_message_id}"
                else:
                    import hashlib
                    clean_from = self.clean_phone_number(from_number)
                    hash_body = hashlib.sha1((message_text or '').encode('utf-8')).hexdigest()[:16]
                    fingerprint = f"wa:{clean_from}:{timestamp}:{hash_body}"
                _logger.info(f"Generated fingerprint: {fingerprint}")
            except Exception as e:
                _logger.warning(f"Error generating fingerprint: {str(e)}")
                fingerprint = f"wa:{self.clean_phone_number(from_number)}:{timestamp}"
            
            # De-dup on this record
            MailMessage = request.env['mail.message'].sudo()
            existing = MailMessage.search([
                ('model', '=', record._name),
                ('res_id', '=', record.id),
                ('message_id', '=', fingerprint),
            ], limit=1)
            
            if existing:
                _logger.info("Message already exists, skipping duplicate")
                return
            
            # Prepare body
            if message_type == 'text':
                message_body = f"{message_text}"
            else:
                message_body = f"WhatsApp {message_type.title()}: {message_text}"
            
            _logger.info(f"Message body: {message_body[:100]}...")
            
            post_kwargs = {
                'body': message_body,
                'message_type': "comment",
                'subtype_xmlid': "mail.mt_comment",
                'message_id': fingerprint,
            }
            if author_partner:
                post_kwargs['author_id'] = author_partner.id
                _logger.info(f"Using author partner ID: {author_partner.id}")
            
            _logger.info(f"Posting message with kwargs: {post_kwargs}")
            record.message_post(**post_kwargs)
            _logger.info("Message posted to record successfully")

            # Also reflect in discuss channel if it exists
            try:
                _logger.info("Attempting to log to Discuss channel...")
                result = request.env['whatsapp.logger'].log_incoming_if_exists(author_partner, message_body, fingerprint, context_id)
                if result:
                    _logger.info("Message also logged to Discuss channel")
                else:
                    _logger.warning("Failed to log to Discuss channel")
            except Exception as e:
                _logger.error(f"Error logging to Discuss channel: {str(e)}")
                _logger.error(f"Traceback: {traceback.format_exc()}")
        
        except Exception as e:
            _logger.error(f"=== RECORD LOGGING ERROR ===")
            _logger.error(f"Error logging message on record: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Record: {record._name} (ID: {record.id})")
            _logger.error(f"From number: {from_number}")
            _logger.error(f"Message text: {message_text}")

    def find_partner_by_phone(self, phone_number):
        """Find res.partner by phone or mobile using digits-only and suffix matching"""
        try:
            _logger.info(f"=== SEARCHING PARTNER BY PHONE ===")
            _logger.info(f"Original phone number: {phone_number}")
            
            clean_phone = self.clean_phone_number(phone_number)
            _logger.info(f"Cleaned phone: {clean_phone}")
            
            if not clean_phone:
                _logger.warning("No clean phone number to search with")
                return False
                
            env = request.env
            cr = env.cr
            Partner = env['res.partner'].sudo()
            
            def _fetch_one(sql, params):
                try:
                    _logger.info(f"With params: {params}")
                    cr.execute(sql, params)
                    row = cr.fetchone()
                    if row:
                        rec = Partner.browse(row[0])
                        if rec.exists():
                            _logger.info(f"Found partner: {rec.name} (ID: {rec.id})")
                            return rec
                    _logger.info("No partner found with this query")
                    return False
                except Exception as e:
                    _logger.error(f"SQL execution error: {str(e)}")
                    return False
            
            # Exact match on digits-only
            _logger.info("Trying exact match...")
            sql_exact = """
                SELECT id FROM res_partner
                WHERE regexp_replace(coalesce(phone,''), '[^0-9]', '', 'g') = %s
                   OR regexp_replace(coalesce(mobile,''), '[^0-9]', '', 'g') = %s
                ORDER BY id DESC
                LIMIT 1
            """
            partner = _fetch_one(sql_exact, [clean_phone, clean_phone])
            if partner:
                _logger.info("Found partner with exact match")
                return partner
            
            # Last-10 equality
            last10 = clean_phone[-10:] if len(clean_phone) >= 10 else clean_phone
            _logger.info(f"Trying last-10 match with: {last10}")
            if last10 and last10 != clean_phone:
                sql_last10 = """
                    SELECT id FROM res_partner
                    WHERE regexp_replace(coalesce(phone,''), '[^0-9]', '', 'g') = %s
                       OR regexp_replace(coalesce(mobile,''), '[^0-9]', '', 'g') = %s
                ORDER BY id DESC
                LIMIT 1
                """
                partner = _fetch_one(sql_last10, [last10, last10])
                if partner:
                    _logger.info("Found partner with last-10 match")
                    return partner
            
            # Suffix LIKE last-10
            _logger.info(f"Trying suffix LIKE match with: %{last10}")
            if last10:
                sql_like = """
                    SELECT id FROM res_partner
                    WHERE regexp_replace(coalesce(phone,''), '[^0-9]', '', 'g') LIKE %s
                       OR regexp_replace(coalesce(mobile,''), '[^0-9]', '', 'g') LIKE %s
                ORDER BY id DESC
                LIMIT 1
                """
                like_param = f"%{last10}"
                partner = _fetch_one(sql_like, [like_param, like_param])
                if partner:
                    _logger.info("Found partner with suffix LIKE match")
                    return partner
            
            _logger.info("No partner found with any matching method")
            return False
        except Exception as e:
            _logger.error(f"=== PARTNER SEARCH ERROR ===")
            _logger.error(f"Error searching partner by phone: {str(e)}")
            _logger.error(f"Traceback: {traceback.format_exc()}")
            _logger.error(f"Phone number: {phone_number}")
            return False
