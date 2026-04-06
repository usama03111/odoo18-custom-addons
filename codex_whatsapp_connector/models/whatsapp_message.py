# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class WhatsAppMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message'

    msg_uid = fields.Char(string="WhatsApp Message ID")
    wa_account_id = fields.Many2one('whatsapp.account', string="WhatsApp Account")
    wa_template_id = fields.Many2one('whatsapp.template', string="WhatsApp Template")
    mail_message_id = fields.Many2one('mail.message', string="Mail Message")
    state = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('sent', 'Sent'),
        ('exception', 'Exception'),
        ('error', 'Error'),
        ('cancel', 'Cancelled'),
        ('received', 'Received'),
        ('read', 'Read'),
    ], string="State", default='outgoing')
    mobile_number_formatted = fields.Char(string="Mobile Number")
    
    # Supported attachment types for header
    _SUPPORTED_ATTACHMENT_TYPE = {
        'image': ['image/jpeg', 'image/png'],
        'video': ['video/mp4', 'video/3gpp'],
        'document': ['application/pdf', 'application/vnd.ms-powerpoint', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/plain'],
        'audio': ['audio/aac', 'audio/mp4', 'audio/mpeg', 'audio/amr', 'audio/ogg'], 
    }

    def _prepare_attachment_vals(self, attachment, wa_account_id=False):
        """ Prepare attachment values for WhatsApp API """
        return {
            'link': attachment.url,
            'filename': attachment.name,
        }
