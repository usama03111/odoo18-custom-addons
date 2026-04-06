# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields

class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_project_expiry_notification = fields.Boolean(
        string="Expiry Notification", related='company_id.sh_project_expiry_notification', readonly=False)
    sh_is_project_notify_customer = fields.Boolean(
        string="Notify Customer", related='company_id.sh_is_project_notify_customer', readonly=False)
    sh_project_on_date_notify = fields.Boolean(
        string="On Date Notification", related='company_id.sh_project_on_date_notify', readonly=False)
    project_enter_before_first_notify = fields.Integer(
        " Notify Before Expiry Date", related='company_id.project_enter_before_first_notify', readonly=False)
    project_enter_before_second_notify = fields.Integer(
        "Notify Before Expiry Date ", related='company_id.project_enter_before_second_notify', readonly=False)
    project_enter_before_third_notify = fields.Integer(
        string=" Notify Before Expiry Date ", related='company_id.project_enter_before_third_notify', readonly=False)
    project_enter_after_first_notify = fields.Integer(
        string=" Notify After Expiry Date", related='company_id.project_enter_after_first_notify', readonly=False)
    project_enter_after_second_notify = fields.Integer(
        string="Notify After Expiry Date ", related='company_id.project_enter_after_second_notify', readonly=False)
    project_enter_after_third_notify = fields.Integer(
        string=" Notify After Expiry Date ", related='company_id.project_enter_after_third_notify', readonly=False)
    project_attachment_email = fields.Char(string="Email to", related='company_id.project_attachment_email', readonly=False)
