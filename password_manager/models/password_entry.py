from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from cryptography.fernet import Fernet
import logging

_logger = logging.getLogger(__name__)

class PasswordEntry(models.Model):
    _name = 'password.entry'
    _description = 'Password Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Title', required=True, tracking=True)
    url = fields.Char(string='URL', tracking=True)
    username = fields.Char(string='Username', tracking=True)
    password_encrypted = fields.Char(string='Encrypted Password')
    password = fields.Char(string='Password', compute='_compute_password', inverse='_inverse_password', store=False)
    notes = fields.Text(string='Notes')
    tags = fields.Many2many('password.tag',string='Tags')
    user_ids = fields.Many2many('res.users', string='Authorized Users', help='Users authorized to view this password')
    
    # Virtual field to toggle visibility in UI (not stored)
    show_password = fields.Boolean(default=False)

    def _get_encryption_key(self):
        param = self.env['ir.config_parameter'].sudo().get_param('password_manager.encryption_key')
        if not param:
            key = Fernet.generate_key()
            self.env['ir.config_parameter'].sudo().set_param('password_manager.encryption_key', key.decode())
            return key
        return param.encode()
    
    def _encrypt(self, txt):
        if not txt:
            return False
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(txt.encode()).decode()

    def _decrypt(self, txt):
        if not txt:
            return False
        key = self._get_encryption_key()
        f = Fernet(key)
        try:
            return f.decrypt(txt.encode()).decode()
        except Exception as e:
            _logger.error("Decryption failed: %s", e)
            return "Decryption Failed"

    @api.depends('password_encrypted')
    def _compute_password(self):
        for record in self:
            # check_access_rights Verify that the given operation is allowed for the current user accord to ir.model.access.
            if record.check_access_rights('read', raise_exception=False) and record._check_authorization():
                 record.password = record._decrypt(record.password_encrypted) if record.password_encrypted else ""
            else:
                 record.password = "********"

    def _inverse_password(self):
        for record in self:
            if record.password:
                record.password_encrypted = record._encrypt(record.password)

    def _check_authorization(self):
        self.ensure_one()
        if self.env.is_superuser():
            return True
        if self.create_uid == self.env.user or self.env.user in self.user_ids:
            return True
        return False

    def action_reveal(self):
        self.ensure_one()
        if not self._check_authorization():
             raise AccessError(_("You are not authorized to access this credential."))
        
        # Log the access
        self.message_post(body=_("User %s revealed the password.", self.env.user.name))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Password Revealed'),
                'message': _('Password: %s', self.password), # This shows in a notification
                'sticky': True,
            }
        }
    
    
    def action_copy_password(self):
        self.ensure_one()
        if not self._check_authorization():
             raise AccessError(_("You are not authorized to copy this credential."))

        self.message_post(body=_("User %s copied the password.", self.env.user.name))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'password_manager.copy_to_clipboard',
            'params': {
                'password': self.password,
            }
        }


class PasswordTag(models.Model):
    _name = 'password.tag'
    _description = 'Password Tag'

    name = fields.Char('Name', required=True)
    color = fields.Integer('Color')
