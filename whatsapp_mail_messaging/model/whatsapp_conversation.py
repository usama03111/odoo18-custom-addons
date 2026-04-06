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
from odoo import api, fields, models
from datetime import datetime


class WhatsappConversation(models.Model):
    """ WhatsApp Conversation Model """
    _name = 'whatsapp.conversation'
    _description = 'WhatsApp Conversation'
    _order = 'last_message_date desc'

    name = fields.Char(string="Conversation Name", compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    mobile = fields.Char(string="Mobile Number", required=True)
    last_message_date = fields.Datetime(string="Last Message", default=fields.Datetime.now)
    message_count = fields.Integer(string="Message Count", compute='_compute_message_count', store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string="Status", default='active')
    
    message_ids = fields.One2many('whatsapp.message', 'conversation_id', string="Messages")
    new_message = fields.Text(string="New Message", help="Type your message here")
    
    @api.depends('partner_id', 'mobile')
    def _compute_name(self):
        for record in self:
            if record.partner_id:
                record.name = f"{record.partner_id.name} ({record.mobile})"
            else:
                record.name = f"Unknown ({record.mobile})"
    
    @api.depends('message_ids')
    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.message_ids)
    
    def action_view_messages(self):
        """ Open chat view for this conversation """
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.conversation',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('whatsapp_mail_messaging.whatsapp_conversation_chat_view').id,
            'target': 'new',
        }
    
    def action_send_message(self):
        """ Send a new message from the chat view """
        if hasattr(self, 'new_message') and self.new_message:
            # Create a new message record
            self.env['whatsapp.message'].create({
                'conversation_id': self.id,
                'message_type': 'sent',
                'message_content': self.new_message,
                'message_date': fields.Datetime.now(),
            })
            
            # Update conversation last message date
            self.write({
                'last_message_date': fields.Datetime.now(),
            })
            
            # Clear the input field
            self.new_message = False
            
            # Redirect to WhatsApp Web to send the message
            message_string = self.new_message.replace(' ', '%20')
            return {
                'type': 'ir.actions.act_url',
                'url': f"https://api.whatsapp.com/send?phone={self.mobile}&text={message_string}",
                'target': 'new',
            }
        return True


class WhatsappMessage(models.Model):
    """ WhatsApp Message Model """
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message'
    _order = 'message_date asc'

    conversation_id = fields.Many2one('whatsapp.conversation', string="Conversation", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Customer", related='conversation_id.partner_id', store=True)
    mobile = fields.Char(string="Mobile Number", related='conversation_id.mobile', store=True)
    
    message_type = fields.Selection([
        ('sent', 'Sent'),
        ('received', 'Received')
    ], string="Message Type", required=True)
    
    message_content = fields.Text(string="Message Content", required=True)
    message_date = fields.Datetime(string="Message Date", default=fields.Datetime.now)
    message_id = fields.Char(string="WhatsApp Message ID", help="External WhatsApp message ID")
    
    # Media fields
    has_media = fields.Boolean(string="Has Media")
    media_type = fields.Selection([
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document')
    ], string="Media Type")
    media_url = fields.Char(string="Media URL")
    
    def name_get(self):
        """ Custom name display """
        result = []
        for record in self:
            name = f"{record.message_type.title()} - {record.message_date.strftime('%Y-%m-%d %H:%M')}"
            result.append((record.id, name))
        return result 