# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, tools

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        if template_id and composition_mode == 'mass_mail':
            template = self.env['mail.template'].browse(template_id)
            fields = ['subject', 'body_html',
                      'email_from', 'reply_to', 'mail_server_id']
            values = dict((field, getattr(template, field))
                          for field in fields if getattr(template, field))

            if template.attachment_ids:
                values['attachment_ids'] = [att.id for att in template.attachment_ids]
            if template.mail_server_id:
                values['mail_server_id'] = template.mail_server_id.id
            if template.user_signature and 'body_html' in values:
                signature = self.env.user.signature
                values['body_html'] = tools.append_content_to_html(
                    values['body_html'], signature, plaintext=False)
        elif template_id:
            values = self.generate_email_for_composer(
                template_id, [res_id],
                ['subject', 'body_html', 'email_from', 'email_to', 'partner_to',
                    'email_cc',  'reply_to', 'attachment_ids', 'mail_server_id']
            )[res_id]
            template = self.env['mail.template'].browse(template_id)
            if template:
                attach = self.env['ir.attachment'].search(
                    [('res_id', '=', res_id), ('res_model', '=', 'project.task')])

                for rec in attach:
                    values.setdefault('attachment_ids', list()).append(rec.id)

            sh_attachment = self.env['ir.attachment']
            for attach_fname, attach_datas in values.pop('attachments', []):
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'datas_fname': attach_fname,
                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                }
                values.setdefault('attachment_ids', list()).append(sh_attachment.create(data_attach).id)
        else:
            default_values = self.with_context(default_composition_mode=composition_mode, default_model=model, default_res_id=res_id).default_get(
                ['composition_mode', 'model', 'res_id', 'parent_id', 'partner_ids', 'subject', 'body', 'email_from', 'reply_to', 'attachment_ids', 'mail_server_id'])
            values = dict((key, default_values[key]) for key in [
                          'subject', 'body', 'partner_ids', 'email_from', 'reply_to', 'attachment_ids', 'mail_server_id'] if key in default_values)

        if values.get('body_html'):
            values['body'] = values.pop('body_html')
        values = self._convert_to_write(values)
        return {'value': values}
