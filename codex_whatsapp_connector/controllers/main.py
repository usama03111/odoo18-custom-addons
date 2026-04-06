from odoo import http
from odoo.http import request
import requests
import json
import logging
from odoo import fields
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class WhatsAppController(http.Controller):

    @http.route('/whatsapp/send_message', type='json', auth='user')
    def send_message(self, res_model, res_id, message):
        try:
            # Fetch the record
            record = request.env[res_model].browse(res_id)
            if not record.exists():
                return {"error": "Record not found"}

            # Get WhatsApp Account (use the first active one for now)
            wa_account = request.env['whatsapp.account'].sudo().search([], limit=1)
            if not wa_account:
                return {"error": "No WhatsApp Business Account configured. Please create one in WhatsApp > Configuration > Accounts."}
            
            access_token = wa_account.token
            phone_number_id = wa_account.phone_uid
            # Default to v22.0 if not specified (could be added to account model later)
            api_version = "v22.0" 
            
            if not access_token or not phone_number_id:
                return {"error": "Incomplete WhatsApp Account configuration. Check Token and Phone ID."}
            
            # Get recipient phone number based on record type
            recipient_number = None
            partner = None
            
            # Comprehensive phone number detection for multiple modules
            recipient_number, partner = self._get_phone_number_and_partner(record, res_model)

            if not recipient_number:
                return {"error": "No phone number found for this record"}

            # Format phone number exactly like Meta expects (remove + and spaces)
            recipient_number = recipient_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")

            # Check if we can send free-form messages to this customer
            can_send_free_form = self._can_send_free_form_message(recipient_number, partner)
            
            template_name = 'hello_world'
            template_language = 'en_US'

            # If using template, validate template existence
            if not can_send_free_form:
                # Find a suitable template (e.g., hello_world) for this account
                template = request.env['whatsapp.template'].sudo().search([
                    ('wa_account_id', '=', wa_account.id),
                    ('name', '=', 'hello_world'),
                    ('status', '=', 'approved')
                ], limit=1)
                
                if not template:
                     # Fallback to any approved template or error
                     template = request.env['whatsapp.template'].sudo().search([
                        ('wa_account_id', '=', wa_account.id),
                        ('status', '=', 'approved')
                     ], limit=1)
                
                if template:
                    template_name = template.name
                    template_language = template.lang_code or 'en_US'
                else:
                    return {"error": "No approved WhatsApp Template found for this account (required for first contact)."}
            
            url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            if can_send_free_form:
                # Send free-form message (customer has messaged us within 24 hours)
                payload = {
                    "messaging_product": "whatsapp",
                    "to": recipient_number,
                    "type": "text",
                    "text": {
                        "body": message
                    }
                }
                message_type = "free_form"
            else:
                # Send template message for first contact
                payload = {
                    "messaging_product": "whatsapp",
                    "to": recipient_number,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {
                            "code": template_language
                        }
                    }
                }
                message_type = "template"

            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # Parse the response to get detailed error information
            wa_message_id = None
            try:
                response_data = response.json()
                # Typical success payload: {"messages":[{"id":"wamid.HBg..."}]}
                if isinstance(response_data, dict) and response.status_code == 200:
                    try:
                        wa_message_id = (response_data.get('messages') or [{}])[0].get('id')
                    except Exception:
                        wa_message_id = None
                
            except json.JSONDecodeError:
                _logger.error("Could not parse response as JSON")

            # Log in chatter
            if response.status_code == 200:
                # Create a properly formatted plain text message for the chatter
                chatter_message = f"""{message}"""
                if message_type == "template":
                    chatter_message += f"\n(Sent as template: {template_name})"
                
                # Post message in chatter, store WA message id in mail.message.message_id for reply mapping
                post_kwargs = {
                    'body': chatter_message,
                    'message_type': "comment",
                    'subtype_xmlid': "mail.mt_comment",
                }
                if wa_message_id:
                    post_kwargs['message_id'] = f"wa:{wa_message_id}"
                    _logger.info(f"Stored WhatsApp message ID for reply threading: wa:{wa_message_id}")
                result = record.message_post(**post_kwargs)

                # Also log to a dedicated Discuss channel for the partner (if not already in a Discuss channel)
                try:
                    logger = request.env['whatsapp.logger']
                    if partner and res_model != 'discuss.channel':
                        # Only log to Discuss if we're not already in a Discuss channel
                        fingerprint = post_kwargs.get('message_id') or f"wa:out:{record.id}:{fields.Datetime.now()}"
                        logger.log_to_channel(partner, chatter_message, fingerprint, is_incoming=False, origin_model=res_model, origin_res_id=record.id, origin_name=getattr(record, 'display_name', None))
                except Exception as e:
                    _logger.warning(f"Channel logging failed: {str(e)}")
                
                return {"success": True, "message_type": message_type}
            else:
                error_data = response.json() if response.text else {"error": "Unknown API error"}
                error_message = json.dumps(error_data)
                
                # Check if the error is about needing approval for text messages
                if "does not support this operation" in error_message or "permissions" in error_message.lower():
                    return {
                        "error": "WhatsApp API Error: Your account may not have permission to send free-form text messages. You may need to: 1) Get approval from Meta for text messages, 2) Use approved templates instead, or 3) Contact Meta support to enable text messaging."
                    }
                elif response.status_code == 400:
                    # Template-specific error
                    return {
                        "error": f"WhatsApp Template Error (400): {error_message}. This usually means: 1) Template name '{template_name}' doesn't exist, 2) Template is not approved, 3) Template format is incorrect. Please check your template settings."
                    }
                else:
                    return {
                        "error": f"WhatsApp API error: {error_message}"
                    }
        except Exception as e:
            _logger.error(f"WhatsApp Controller Error: {str(e)}")
            return {"error": f"Server error: {str(e)}"}

    def _get_phone_number_and_partner(self, record, res_model):
        """
        Comprehensive method to get phone number and partner from various Odoo models.
        Returns tuple (phone_number, partner) or (None, None) if not found.
        """
        try:
            # CRM Module
            if res_model == 'crm.lead':
                recipient_number = record.phone or record.mobile
                partner = record.partner_id
                if recipient_number and partner:
                    return recipient_number, partner
            
            # Discuss/Channel Module
            elif res_model == 'discuss.channel':
                if hasattr(record, 'wa_customer_partner_id') and record.wa_customer_partner_id:
                    partner = record.wa_customer_partner_id
                    recipient_number = partner.phone or partner.mobile
                    if recipient_number:
                        return recipient_number, partner
                else:
                    # Fallback: try to get partner from channel members
                    user_partner = request.env.user.partner_id
                    customer_partners = record.channel_partner_ids.filtered(lambda p: p.id != user_partner.id)
                    if customer_partners:
                        partner = customer_partners[0]
                        recipient_number = partner.phone or partner.mobile
                        if recipient_number:
                            return recipient_number, partner
            
            # Sales Module
            elif res_model == 'sale.order':
                partner = record.partner_id
                if partner:
                    recipient_number = partner.phone or partner.mobile
                    if recipient_number:
                        return recipient_number, partner
            
            # Project Module
            elif res_model == 'project.project':
                partner = record.partner_id
                if partner:
                    recipient_number = partner.phone or partner.mobile
                    if recipient_number:
                        return recipient_number, partner
            
            # Project Task Module
            elif res_model == 'project.task':
                partner = record.partner_id
                if partner:
                    recipient_number = partner.phone or partner.mobile
                    if recipient_number:
                        return recipient_number, partner
            
            # Purchase Module
            elif res_model == 'purchase.order':
                partner = record.partner_id
                if partner:
                    recipient_number = partner.phone or partner.mobile
                    if recipient_number:
                        return recipient_number, partner
            
            # Account/Invoice Module
            elif res_model in ['account.move', 'account.invoice']:
                partner = record.partner_id
                if partner:
                    recipient_number = partner.phone or partner.mobile
                    if recipient_number:
                        return recipient_number, partner
            
            # Generic Partner-based models (fallback)
            else:
                # Try to find partner field in the record
                partner_fields = ['partner_id', 'customer_id', 'client_id', 'contact_id']
                for field_name in partner_fields:
                    if hasattr(record, field_name) and getattr(record, field_name):
                        partner = getattr(record, field_name)
                        recipient_number = partner.phone or partner.mobile
                        if recipient_number:
                            return recipient_number, partner
                
                # Try to find phone fields directly on the record
                phone_fields = ['phone', 'mobile', 'telephone', 'contact_phone']
                for field_name in phone_fields:
                    if hasattr(record, field_name) and getattr(record, field_name):
                        recipient_number = getattr(record, field_name)
                        # Try to find associated partner
                        if hasattr(record, 'partner_id') and record.partner_id:
                            partner = record.partner_id
                        else:
                            partner = None
                        if recipient_number:
                            return recipient_number, partner
            
            return None, None
            
        except Exception as e:
            _logger.error(f"Error getting phone number and partner for {res_model}: {str(e)}")
            return None, None

    def _can_send_free_form_message(self, phone_number, partner):
        """
        Check if we can send free-form messages to this customer.
        Returns True only if there is activity in the last 24 hours.
        Logic:
        - Direct incoming messages from the partner INSIDE related Discuss channels within 24h
        - OR latest message timestamp in any related Discuss channel within 24h
        """
        try:
            if not partner:
                return False
            
            cutoff_time = fields.Datetime.now() - timedelta(hours=24)
            user_partner_id = request.env.user.partner_id.id

            # Collect related channel ids (WA-flag or membership)
            Channel = request.env['discuss.channel'].sudo()
            channel_model_name = Channel._name or 'discuss.channel'

            channels_flag = Channel.search([('wa_customer_partner_id', '=', partner.id),
                                            ('is_whatsapp','=', True),
                                            ('channel_type','=','channel')])

            member_channel_ids = []
            MemberModel = request.env.get('discuss.channel.member')
            if MemberModel is not None:
                member_records = MemberModel.sudo().search([('partner_id', '=', partner.id)])
                member_channel_ids = member_records.mapped('channel_id.id')
            else:
                try:
                    channels_member = Channel.search([('channel_partner_ids', 'in', partner.id)])
                    member_channel_ids = channels_member.ids
                except Exception:
                    member_channel_ids = []

            all_channel_ids = list({*channels_flag.ids, *member_channel_ids})
            if all_channel_ids:
                # 1) Direct incoming messages from the partner inside these channels
                try:
                    partner_msgs = request.env['mail.message'].sudo().search([
                        ('model', '=', channel_model_name),
                        ('res_id', 'in', all_channel_ids),
                        ('author_id', '=', partner.id),
                        ('create_date', '>=', cutoff_time),
                    ], limit=1)
                except Exception as e:
                    _logger.warning(f"Partner message search in channels failed: {str(e)}")
                    partner_msgs = False
                if partner_msgs:
                    return True

                # 2) Latest message across those channels
                try:
                    last_msg = request.env['mail.message'].sudo().search([
                        ('model', '=', channel_model_name),
                        ('res_id', 'in', all_channel_ids)
                    ], order='create_date desc', limit=1)
                except Exception as e:
                    _logger.warning(f"Channel last message search failed: {str(e)}")
                    last_msg = False
                if last_msg and last_msg.create_date and last_msg.create_date >= cutoff_time:
                    return True

            return False

        except Exception as e:
            _logger.error(f"Error checking free-form message permission: {str(e)}")
            # Default to False (use template) if there are any errors
            return False


    @http.route('/whatsapp/send_media', type='json', auth='user')
    def send_media(self, res_model, res_id, filename, mimetype, data_base64, caption=None):
        try:
            record = request.env[res_model].browse(res_id)
            if not record.exists():
                return {"error": "Record not found"}

            # Get WhatsApp Account
            wa_account = request.env['whatsapp.account'].sudo().search([], limit=1)
            if not wa_account:
                return {"error": "No WhatsApp Business Account configured. Please create one in WhatsApp > Configuration > Accounts."}
            
            access_token = wa_account.token
            phone_number_id = wa_account.phone_uid
            api_version = "v22.0"

            if not access_token or not phone_number_id:
                return {"error": "Incomplete WhatsApp Account configuration. Check Token and Phone ID."}

            # Determine recipient
            recipient_number, partner = self._get_phone_number_and_partner(record, res_model)
            if not recipient_number:
                return {"error": "No phone number found for this record"}
            recipient_number = recipient_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")

            # Upload media to WhatsApp
            import base64
            try:
                binary = base64.b64decode(data_base64)
            except Exception:
                return {"error": "Invalid file data"}

            upload_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/media"
            up_headers = {"Authorization": f"Bearer {access_token}"}
            files = {
                'file': (filename, binary, mimetype),
            }
            data = {
                'messaging_product': 'whatsapp',
            }
            up_resp = requests.post(upload_url, headers=up_headers, files=files, data=data)
            if up_resp.status_code != 200:
                try:
                    return {"error": f"Media upload failed: {up_resp.json()}"}
                except Exception:
                    return {"error": f"Media upload failed: {up_resp.text}"}
            media_id = up_resp.json().get('id')
            if not media_id:
                return {"error": "Media upload did not return an id"}

            # Prepare message payload
            send_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            msg_type = 'document'
            media_key = 'document'
            mt = (mimetype or '').lower()
            if mt.startswith('image/'):
                msg_type = 'image'
                media_key = 'image'
            elif mt.startswith('audio/'):
                msg_type = 'audio'
                media_key = 'audio'
            elif mt.startswith('video/'):
                msg_type = 'video'
                media_key = 'video'

            payload = {
                'messaging_product': 'whatsapp',
                'to': recipient_number,
                'type': msg_type,
                media_key: {
                    'id': media_id,
                }
            }
            if caption and msg_type in ('image', 'video', 'document'):
                payload[media_key]['caption'] = caption
            if msg_type == 'document' and filename:
                payload[media_key]['filename'] = filename
            # Mark as voice note when sending OGG/Opus audio
            if msg_type == 'audio' and (mt == 'audio/ogg' or mt == 'audio/opus' or mt == 'audio/ogg; codecs=opus'):
                try:
                    payload[media_key]['voice'] = True
                except Exception:
                    pass

            resp = requests.post(send_url, headers=headers, data=json.dumps(payload))

            if resp.status_code == 200:
                # Log to chatter
                body = (caption or '').strip()
                post_kwargs = {
                    'body': body,
                    'message_type': "comment",
                    'subtype_xmlid': "mail.mt_comment",
                }
                try:
                    response_data = resp.json()
                    wa_message_id = (response_data.get('messages') or [{}])[0].get('id')
                    if wa_message_id:
                        post_kwargs['message_id'] = f"wa:{wa_message_id}"
                except Exception:
                    pass

                # Create and attach ir.attachment so media displays in chatter
                attachment_ids = []
                try:
                    att = request.env['ir.attachment'].sudo().create({
                        'name': filename or 'file',
                        'datas': data_base64,
                        'mimetype': mimetype or 'application/octet-stream',
                        'res_model': res_model,
                        'res_id': record.id,
                        'type': 'binary',
                    })
                    if att:
                        attachment_ids = [att.id]
                        post_kwargs['attachment_ids'] = attachment_ids
                except Exception as e:
                    _logger.warning(f"Failed to create attachment for media log: {str(e)}")

                record.message_post(**post_kwargs)
                # Also log to discuss channel
                try:
                    logger = request.env['whatsapp.logger']
                    if partner and res_model != 'discuss.channel':
                        fingerprint = post_kwargs.get('message_id') or f"wa:out:{record.id}:{fields.Datetime.now()}"
                        caption_msg = body
                        # Log to Discuss channel without attachment display
                        logger.log_to_channel(partner, caption_msg, fingerprint, is_incoming=False,
                                              attachment_ids=attachment_ids, origin_model=res_model, origin_res_id=record.id, origin_name=getattr(record, 'display_name', None))
                except Exception as e:
                    _logger.warning(f"Channel logging failed: {str(e)}")

                return {"success": True, "message_type": msg_type}
            else:
                try:
                    return {"error": f"WhatsApp API error: {resp.json()}"}
                except Exception:
                    return {"error": f"WhatsApp API error: {resp.text}"}
        except Exception as e:
            _logger.error(f"send_media error: {str(e)}")
            return {"error": f"Server error: {str(e)}"}
