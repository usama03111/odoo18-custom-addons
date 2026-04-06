# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http, fields
from odoo.http import request
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class SendMessage(http.Controller):
    """ Controller for whatsapp message templates """
    @http.route('/whatsapp_message', type='json', auth='public')
    def whatsapp_message(self, **kwargs):
        """ Whatsapp message templates """
        messages = request.env['selection.message'].sudo().search_read(
            fields=['name', 'message'])
        return {'messages': messages}

    @http.route('/mobile_number', type='json', auth='public')
    def mobile_number(self, **kwargs):
        """ Mobile number of website """
        mobile_number = request.env['website'].sudo().search_read(
            fields=['mobile_number']
        )
        return {'mobile': mobile_number}
    
    @http.route('/whatsapp/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def whatsapp_webhook(self, **kwargs):
        """ Webhook to receive WhatsApp messages """
        try:
            # Get the raw data from the request
            data = request.httprequest.get_data()
            _logger.info(f"WhatsApp webhook received: {data}")
            
            # Parse the JSON data
            webhook_data = json.loads(data)
            
            # Process the webhook data
            self._process_whatsapp_webhook(webhook_data)
            
            return 'OK', 200
        except Exception as e:
            _logger.error(f"Error processing WhatsApp webhook: {str(e)}")
            return 'Error', 500
    
    def _process_whatsapp_webhook(self, webhook_data):
        """ Process incoming WhatsApp messages """
        try:
            # Check if WhatsApp API is enabled
            api_enabled = self.env['ir.config_parameter'].sudo().get_param('whatsapp_mail_messaging.whatsapp_api_enabled', 'False')
            if api_enabled != 'True':
                _logger.warning("WhatsApp API integration is not enabled")
                return
            
            # Get API provider
            api_provider = self.env['ir.config_parameter'].sudo().get_param('whatsapp_mail_messaging.whatsapp_api_provider', 'twilio')
            
            # Process based on provider
            if api_provider == 'twilio':
                if 'Body' in webhook_data:
                    self._process_twilio_message(webhook_data)
            elif api_provider == 'whatsapp_business':
                if 'entry' in webhook_data:
                    for entry in webhook_data['entry']:
                        if 'changes' in entry:
                            for change in entry['changes']:
                                if change.get('value', {}).get('messages'):
                                    for message in change['value']['messages']:
                                        self._process_single_message(message)
            else:
                # Generic processing for custom API
                if 'entry' in webhook_data:
                    for entry in webhook_data['entry']:
                        if 'changes' in entry:
                            for change in entry['changes']:
                                if change.get('value', {}).get('messages'):
                                    for message in change['value']['messages']:
                                        self._process_single_message(message)
                elif 'Body' in webhook_data:
                    self._process_twilio_message(webhook_data)
                
        except Exception as e:
            _logger.error(f"Error processing webhook data: {str(e)}")
    
    def _process_single_message(self, message_data):
        """ Process a single WhatsApp message """
        try:
            # Extract message details
            from_number = message_data.get('from', '')
            message_text = message_data.get('text', {}).get('body', '')
            message_id = message_data.get('id', '')
            timestamp = message_data.get('timestamp', '')
            
            # Find or create conversation
            conversation = self._get_or_create_conversation(from_number)
            
            # Create message record
            if conversation and message_text:
                self.env['whatsapp.message'].sudo().create({
                    'conversation_id': conversation.id,
                    'message_type': 'received',
                    'message_content': message_text,
                    'message_date': datetime.fromtimestamp(int(timestamp)),
                    'message_id': message_id,
                })
                
                # Update conversation last message date
                conversation.sudo().write({
                    'last_message_date': datetime.fromtimestamp(int(timestamp)),
                })
                
        except Exception as e:
            _logger.error(f"Error processing single message: {str(e)}")
    
    def _process_twilio_message(self, webhook_data):
        """ Process Twilio WhatsApp message """
        try:
            from_number = webhook_data.get('From', '')
            message_text = webhook_data.get('Body', '')
            message_id = webhook_data.get('MessageSid', '')
            
            # Remove 'whatsapp:' prefix if present
            if from_number.startswith('whatsapp:'):
                from_number = from_number.replace('whatsapp:', '')
            
            # Find or create conversation
            conversation = self._get_or_create_conversation(from_number)
            
            # Create message record
            if conversation and message_text:
                self.env['whatsapp.message'].sudo().create({
                    'conversation_id': conversation.id,
                    'message_type': 'received',
                    'message_content': message_text,
                    'message_date': fields.Datetime.now(),
                    'message_id': message_id,
                })
                
                # Update conversation last message date
                conversation.sudo().write({
                    'last_message_date': fields.Datetime.now(),
                })
                
        except Exception as e:
            _logger.error(f"Error processing Twilio message: {str(e)}")
    
    def _get_or_create_conversation(self, mobile_number):
        """ Get or create a conversation for the given mobile number """
        try:
            # Clean the mobile number
            mobile_number = self._clean_mobile_number(mobile_number)
            
            # Try to find existing conversation
            conversation = self.env['whatsapp.conversation'].sudo().search([
                ('mobile', '=', mobile_number)
            ], limit=1)
            
            if not conversation:
                # Try to find partner by mobile number
                partner = self.env['res.partner'].sudo().search([
                    ('mobile', '=', mobile_number)
                ], limit=1)
                
                # Create new conversation
                conversation = self.env['whatsapp.conversation'].sudo().create({
                    'partner_id': partner.id if partner else False,
                    'mobile': mobile_number,
                    'last_message_date': fields.Datetime.now(),
                })
            
            return conversation
            
        except Exception as e:
            _logger.error(f"Error getting or creating conversation: {str(e)}")
            return False
    
    def _clean_mobile_number(self, mobile_number):
        """ Clean and format mobile number """
        # Remove common prefixes and non-numeric characters
        cleaned = ''.join(filter(str.isdigit, mobile_number))
        
        # Remove country code if it's +91 (India) and number starts with 91
        if cleaned.startswith('91') and len(cleaned) > 10:
            cleaned = cleaned[2:]
        
        return cleaned
    
    def _get_whatsapp_config(self):
        """ Get WhatsApp configuration parameters """
        config = self.env['ir.config_parameter'].sudo()
        return {
            'api_enabled': config.get_param('whatsapp_mail_messaging.whatsapp_api_enabled', 'False') == 'True',
            'api_provider': config.get_param('whatsapp_mail_messaging.whatsapp_api_provider', 'twilio'),
            'twilio_account_sid': config.get_param('whatsapp_mail_messaging.twilio_account_sid', ''),
            'twilio_auth_token': config.get_param('whatsapp_mail_messaging.twilio_auth_token', ''),
            'twilio_phone_number': config.get_param('whatsapp_mail_messaging.twilio_phone_number', ''),
            'whatsapp_business_token': config.get_param('whatsapp_mail_messaging.whatsapp_business_token', ''),
            'whatsapp_business_phone_id': config.get_param('whatsapp_mail_messaging.whatsapp_business_phone_id', ''),
            'whatsapp_business_webhook_verify_token': config.get_param('whatsapp_mail_messaging.whatsapp_business_webhook_verify_token', ''),
        }
