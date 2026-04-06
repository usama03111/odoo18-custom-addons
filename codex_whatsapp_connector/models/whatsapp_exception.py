# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _

class WhatsAppError(Exception):
    def __init__(self, failure_type, error_code=-1):
        super().__init__(failure_type)
        self.failure_type = failure_type
        self.error_code = error_code
