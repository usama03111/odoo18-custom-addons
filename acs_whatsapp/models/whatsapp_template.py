# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


MESSAGE_TYPE = [
    ('TEXT', 'Message'),
    ('DOCUMENT', 'Document'),
    ('IMAGE', 'Image')
]


class ResLang(models.Model):
    _inherit = 'res.lang'

    acs_whatsapp_code = fields.Char('Language Code')


class whatsappTemplate(models.Model):
    _name = 'acs.whatsapp.template'
    _description = 'whatsapp Template'

    def acs_get_default_lang(self):
        lang = self.env['res.lang'].sudo().search([('code','=',self.env.user.lang)], limit=1)
        return lang

    name = fields.Text(string='Name', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')

    header_message_type = fields.Selection(MESSAGE_TYPE, string='Header Message Type')
    header_message = fields.Text(string='Header Message')
    header_file = fields.Binary(string='Header File')
    header_file_name = fields.Char(string='Header File Name')
    report_id = fields.Many2one('ir.actions.report', string='Report')

    body_message_type = fields.Selection(MESSAGE_TYPE, string='Body Message Type', default='TEXT', required=True)
    body_message = fields.Text(string='Body Message')
    body_file = fields.Binary(string='Body File')
    body_file_name = fields.Char(string='Body File Name')

    footer_message_type = fields.Selection([('TEXT', 'Message')], string='Footer Message Type')
    footer_message = fields.Text(string='Footer Message')
    footer_file = fields.Binary(string='Footer File')
    footer_file_name = fields.Char(string='Footer File Name')

    category = fields.Char("Category", default="TRANSACTIONAL")
    whasaap_id = fields.Char("WhatsApp ID")
    whatsapp_data = fields.Text("Whatsapp Data")
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company)

    partner_ids = fields.Many2many("res.partner", "partner_whatsapp_template_rel", "partner_id", "whatsapp_template_id", "Partners")
    employee_ids = fields.Many2many("hr.employee", "employee_whatsapp_template_rel", "employee_id", "whatsapp_template_id", "Employees")
    language_id = fields.Many2one('res.lang', 'Language', default=acs_get_default_lang)

    def action_approve(self):
        self.state = 'approved'

    def action_draft(self):
        self.state = 'draft'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: