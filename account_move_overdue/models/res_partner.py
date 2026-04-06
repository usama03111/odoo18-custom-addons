from odoo import models, api, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    send_overdue_reminder = fields.Boolean(
        string="Send Overdue Payment Reminder",
        default=True,
        help="If enabled, overdue payment reminder emails will be sent automatically "
             "to this customer."
    )