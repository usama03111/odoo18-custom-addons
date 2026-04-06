# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

class ShIrAttachment(models.Model):
    _inherit = 'ir.attachment'
    _description = 'Ir attachment'

    @api.onchange('sh_is_notify')
    def _onchange_notify(self):
        if self.sh_is_notify:
            check_email = self.env['project.task'].browse(self.res_id)
            if not check_email.partner_id.email:
                raise UserError("Contact Email Not Found!")

    @api.model
    def notify_task_document_expiry(self):
        template = self.env.ref(
            'sh_all_in_one_pms.sh_task_document_expiry_notify_email')
        company_object = self.env['res.company'].search(
            [('sh_task_expiry_notification', '=', True)], limit=1)

        if template and company_object and company_object.sh_task_expiry_notification:
            document_obj = self.search([('res_model', '=', 'project.task')])
            if document_obj:
                for record in document_obj:
                    mail_id = ''
                    partner = self.env['project.task'].browse(record.res_id)
                    record.sh_is_send_mail = False
                    task = self.env['project.task'].browse(record.res_id)
                    record.write({

                        'partner': task.partner_id,
                        'email': record.company_id.task_attachment_email,

                    })

                    if record.expiry_date and record.sh_is_notify and partner.partner_id.email:
                        # On Expiry Date
                        if company_object.sh_task_on_date_notify:

                            if datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date() == datetime.now().date():

                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        # Expiry Date Before First Notify
                        if company_object.task_enter_before_first_notify:

                            before_date = datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) - timedelta(days=company_object.task_enter_before_first_notify)
                            if before_date == datetime.now().date():

                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        # Expiry Date Before Second Notify
                        if company_object.task_enter_before_second_notify:

                            before_date = datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) - timedelta(days=company_object.task_enter_before_second_notify)

                            if before_date == datetime.now().date():
                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        # Expiry Date Before Third Notify
                        if company_object.task_enter_before_third_notify:

                            before_date = datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) - timedelta(days=company_object.task_enter_before_third_notify)

                            if before_date == datetime.now().date():
                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        # Expiry Date After First Notify
                        if company_object.task_enter_after_first_notify:

                            after_date = datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) + timedelta(days=company_object.task_enter_after_first_notify)

                            if after_date == datetime.now().date():
                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        # Expiry Date After Second Notify
                        if company_object.task_enter_after_second_notify:

                            after_date = datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) + timedelta(days=company_object.task_enter_after_second_notify)

                            if after_date == datetime.now().date():
                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        # Expiry Date After Third Notify
                        if company_object.task_enter_after_third_notify:

                            after_date = datetime.strptime(str(record.expiry_date), DEFAULT_SERVER_DATE_FORMAT).date(
                            ) + timedelta(days=company_object.task_enter_after_third_notify)

                            if after_date == datetime.now().date():
                                if template and company_object.sh_task_is_notify_customer and record.partner:
                                    mail_id += record.partner.email
                                    mail_id += ','
                                    record.sh_is_send_mail = True

                                if template and record.company_id.task_attachment_email:
                                    mail_id += record.company_id.task_attachment_email
                                    record.sh_is_send_mail = True

                        if record.sh_is_send_mail:
                            template.send_mail(
                                record.id, email_layout_xmlid='mail.mail_notification_light', force_send=True, email_values={'email_to': mail_id})
