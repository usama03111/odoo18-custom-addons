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
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    """ Inheriting the res config settings to add the whatsapp message field."""
    _inherit = 'res.config.settings'

    whatsapp_message = fields.Char(
        string="WhatsApp Message",
        help="This WhatsApp message template is for sales orders and invoices.",
        config_parameter='whatsapp_mail_messaging.whatsapp_message'
    )
    
    # Alternative: Use a separate field for longer messages
    whatsapp_message_template = fields.Many2one(
        'selection.message',
        string="Default Message Template",
        help="Select a default message template for WhatsApp messages",
        config_parameter='whatsapp_mail_messaging.whatsapp_message_template_id'
    )
    
    # WhatsApp API Configuration
    whatsapp_api_enabled = fields.Boolean(
        string="Enable WhatsApp API Integration", 
        help="Enable webhook to receive WhatsApp messages",
        config_parameter='whatsapp_mail_messaging.whatsapp_api_enabled'
    )
    
    whatsapp_api_provider = fields.Selection([
        ('twilio', 'Twilio'),
        ('whatsapp_business', 'WhatsApp Business API'),
        ('custom', 'Custom API')
    ], 
    string="WhatsApp API Provider", 
    default='twilio',
    config_parameter='whatsapp_mail_messaging.whatsapp_api_provider'
    )
    
    # Twilio Configuration
    twilio_account_sid = fields.Char(
        string="Twilio Account SID",
        config_parameter='whatsapp_mail_messaging.twilio_account_sid'
    )
    
    twilio_auth_token = fields.Char(
        string="Twilio Auth Token",
        config_parameter='whatsapp_mail_messaging.twilio_auth_token'
    )
    
    twilio_phone_number = fields.Char(
        string="Twilio WhatsApp Number",
        config_parameter='whatsapp_mail_messaging.twilio_phone_number'
    )
    
    # WhatsApp Business API Configuration
    whatsapp_business_token = fields.Char(
        string="WhatsApp Business Token",
        config_parameter='whatsapp_mail_messaging.whatsapp_business_token'
    )
    
    whatsapp_business_phone_id = fields.Char(
        string="WhatsApp Business Phone ID",
        config_parameter='whatsapp_mail_messaging.whatsapp_business_phone_id'
    )
    
    whatsapp_business_webhook_verify_token = fields.Char(
        string="Webhook Verify Token",
        config_parameter='whatsapp_mail_messaging.whatsapp_business_webhook_verify_token'
    )
    
    # Webhook URL
    whatsapp_webhook_url = fields.Char(
        string="Webhook URL", 
        compute='_compute_webhook_url', 
        store=False
    )
    
    @api.depends()
    def _compute_webhook_url(self):
        """ Compute the webhook URL for the current instance """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if base_url:
                record.whatsapp_webhook_url = f"{base_url}/whatsapp/webhook"
            else:
                record.whatsapp_webhook_url = "Not configured"
    
    def action_test_webhook(self):
        """ Test the webhook configuration """
        return {
            'type': 'ir.actions.act_url',
            'url': '/whatsapp/webhook',
            'target': 'new',
        }
    
    def action_save_settings(self):
        """ Save the settings and show confirmation """
        # Force save the settings
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_message', self.whatsapp_message or '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_message_template_id', str(self.whatsapp_message_template.id) if self.whatsapp_message_template else '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_api_enabled', str(self.whatsapp_api_enabled))
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_api_provider', self.whatsapp_api_provider or 'twilio')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.twilio_account_sid', self.twilio_account_sid or '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.twilio_auth_token', self.twilio_auth_token or '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.twilio_phone_number', self.twilio_phone_number or '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_business_token', self.whatsapp_business_token or '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_business_phone_id', self.whatsapp_business_phone_id or '')
        self.env['ir.config_parameter'].sudo().set_param('whatsapp_mail_messaging.whatsapp_business_webhook_verify_token', self.whatsapp_business_webhook_verify_token or '')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Settings Saved',
                'message': 'WhatsApp configuration has been saved successfully.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_check_settings(self):
        """ Check current settings """
        config = self.env['ir.config_parameter'].sudo()
        template_id = config.get_param('whatsapp_mail_messaging.whatsapp_message_template_id', '')
        template_name = 'Not set'
        if template_id:
            template = self.env['selection.message'].sudo().browse(int(template_id))
            if template.exists():
                template_name = template.name
        
        settings = {
            'whatsapp_message': config.get_param('whatsapp_mail_messaging.whatsapp_message', 'Not set'),
            'message_template': template_name,
            'api_enabled': config.get_param('whatsapp_mail_messaging.whatsapp_api_enabled', 'False'),
            'api_provider': config.get_param('whatsapp_mail_messaging.whatsapp_api_provider', 'Not set'),
            'twilio_sid': config.get_param('whatsapp_mail_messaging.twilio_account_sid', 'Not set'),
        }
        
        message = f"Current Settings:\n"
        message += f"Quick Message: {settings['whatsapp_message']}\n"
        message += f"Message Template: {settings['message_template']}\n"
        message += f"API Enabled: {settings['api_enabled']}\n"
        message += f"API Provider: {settings['api_provider']}\n"
        message += f"Twilio SID: {settings['twilio_sid']}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Current Settings',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
    
    def action_clear_settings(self):
        """ Clear all WhatsApp settings """
        config = self.env['ir.config_parameter'].sudo()
        config.set_param('whatsapp_mail_messaging.whatsapp_message', '')
        config.set_param('whatsapp_mail_messaging.whatsapp_message_template_id', '')
        config.set_param('whatsapp_mail_messaging.whatsapp_api_enabled', 'False')
        config.set_param('whatsapp_mail_messaging.whatsapp_api_provider', 'twilio')
        config.set_param('whatsapp_mail_messaging.twilio_account_sid', '')
        config.set_param('whatsapp_mail_messaging.twilio_auth_token', '')
        config.set_param('whatsapp_mail_messaging.twilio_phone_number', '')
        config.set_param('whatsapp_mail_messaging.whatsapp_business_token', '')
        config.set_param('whatsapp_mail_messaging.whatsapp_business_phone_id', '')
        config.set_param('whatsapp_mail_messaging.whatsapp_business_webhook_verify_token', '')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Settings Cleared',
                'message': 'All WhatsApp settings have been cleared.',
                'type': 'warning',
                'sticky': False,
            }
        }
