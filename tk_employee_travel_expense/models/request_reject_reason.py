# -*- coding: utf-8 -*-
from odoo import fields, models


class RequestRejectReason(models.Model):
    """
    Model to store predefined reasons for rejecting travel requests.
    """
    _name = "request.reject.reason"
    _description = "Request Reject Reason"
    _rec_name = 'request_reject_reason'

    request_reject_reason = fields.Char(string="Reject Reason", required=True)
    closing_notes = fields.Text(string="Closing Notes")
