# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_task_expiry_notification = fields.Boolean("Expiry Notification")
    sh_task_is_notify_customer = fields.Boolean("Notify Customer")
    sh_task_on_date_notify = fields.Boolean("On Date Notification")
    task_enter_before_first_notify = fields.Integer(
        " Notify Before Expiry Date")
    task_enter_before_second_notify = fields.Integer(
        "Notify Before Expiry Date ")
    task_enter_before_third_notify = fields.Integer(
        " Notify Before Expiry Date ")
    task_enter_after_first_notify = fields.Integer(
        " Notify After Expiry Date")
    task_enter_after_second_notify = fields.Integer(
        "Notify After Expiry Date ")
    task_enter_after_third_notify = fields.Integer(
        " Notify After Expiry Date ")
    task_attachment_email = fields.Char("Email to")
