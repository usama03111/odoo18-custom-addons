# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class WhatsappSendMessage(models.TransientModel):
    """ Wizard for sending whatsapp message."""
    _name = 'whatsapp.send.message'
    _description = 'Whatsapp Send Message'

    partner_id = fields.Many2one('res.partner',
                                 string="Recipient",
                                 help="Partner")
    mobile = fields.Char(string="Contact Number",
                         required=True,
                         help="Contact number of Partner")
    message = fields.Text(string="Message",
                          required=True,
                          help="Message to send")
    image_1920 = fields.Binary(string='Image', help="Image of Partner")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Function for fetching the mobile number and image of partner."""
        self.mobile = self.partner_id.mobile
        self.image_1920 = self.partner_id.image_1920

    def send_message(self):
        """ This function redirects to the whatsapp web with required
        parameters.
        """
        if self.message and self.mobile:
            message_string = ''
            message = self.message.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            message_post_content = message_string
            
            # Create or get conversation
            conversation = self._get_or_create_conversation()
            
            # Create sent message record
            if conversation:
                self.env['whatsapp.message'].create({
                    'conversation_id': conversation.id,
                    'message_type': 'sent',
                    'message_content': self.message,
                    'message_date': fields.Datetime.now(),
                })
                
                # Update conversation last message date
                conversation.write({
                    'last_message_date': fields.Datetime.now(),
                })
            
            if self.partner_id:
                self.partner_id.message_post(body=message_post_content)
            
            # Get WhatsApp configuration
            config = self.env['ir.config_parameter'].sudo()
            api_enabled = config.get_param('whatsapp_mail_messaging.whatsapp_api_enabled', 'False') == 'True'
            api_provider = config.get_param('whatsapp_mail_messaging.whatsapp_api_provider', 'twilio')
            
            # Use API if enabled, otherwise use WhatsApp Web
            if api_enabled and api_provider in ['twilio', 'whatsapp_business']:
                # TODO: Implement API sending
                _logger.info(f"Sending via {api_provider} API")
                return {
                    'type': 'ir.actions.act_url',
                    'url': "https://api.whatsapp.com/send?phone=" + self.mobile +
                           "&text=" + message_string,
                    'target': 'new',
                    'res_id': self.id,
                }
            else:
                # Use WhatsApp Web
                return {
                    'type': 'ir.actions.act_url',
                    'url': "https://api.whatsapp.com/send?phone=" + self.mobile +
                           "&text=" + message_string,
                    'target': 'new',
                    'res_id': self.id,
                }
    
    def _get_or_create_conversation(self):
        """ Get or create a conversation for the current partner and mobile """
        try:
            # Clean the mobile number
            mobile_number = self._clean_mobile_number(self.mobile)
            
            # Try to find existing conversation
            conversation = self.env['whatsapp.conversation'].search([
                ('mobile', '=', mobile_number)
            ], limit=1)
            
            if not conversation:
                # Create new conversation
                conversation = self.env['whatsapp.conversation'].create({
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'mobile': mobile_number,
                    'last_message_date': fields.Datetime.now(),
                })
            
            return conversation
            
        except Exception as e:
            return False
    
    def _clean_mobile_number(self, mobile_number):
        """ Clean and format mobile number """
        # Remove common prefixes and non-numeric characters
        cleaned = ''.join(filter(str.isdigit, mobile_number))
        
        # Remove country code if it's +91 (India) and number starts with 91
        if cleaned.startswith('91') and len(cleaned) > 10:
            cleaned = cleaned[2:]
        
        return cleaned
