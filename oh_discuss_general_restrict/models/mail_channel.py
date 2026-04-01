# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import ValidationError


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    @api.model
    def _get_restricted_channel_ids(self):
        ids_str = self.env['ir.config_parameter'].sudo().get_param(
            'oh_discuss_general_restrict.restricted_channel_ids', default='')
        return set(int(x) for x in ids_str.split(',') if x.strip().isdigit())

    def message_post(self, **kwargs):
        if self._name == 'discuss.channel' and self.ids:
            restricted_ids = self._get_restricted_channel_ids()
            if restricted_ids and any(ch_id in restricted_ids for ch_id in self.ids):
                if not self.env.user.has_group('oh_discuss_general_restrict.group_general_channel_post'):
                    raise ValidationError(_('You are not allowed to post in this channel.'))
        return super(DiscussChannel, self).message_post(**kwargs)
    
    @api.model
    def can_current_user_post(self, channel_ids):
        """Return True if current user can post in all given channels."""
        if not channel_ids:
            return True
        restricted_ids = self._get_restricted_channel_ids()
        if not restricted_ids:
            return True
        if self.env.user.has_group('oh_discuss_general_restrict.group_general_channel_post'):
            return True
        # If any channel is restricted, user cannot post
        return not any(int(ch_id) in restricted_ids for ch_id in channel_ids)
    

