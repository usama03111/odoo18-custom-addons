# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restricted_channel_ids = fields.Many2many(
        'discuss.channel',
        string='Restricted Channels (Posters require group)',
        help='Users must belong to the group "General Channel: Can Post" to post in these channels. Others have read-only access.'
    )

    def set_values(self):
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()
        ids_str = ','.join(str(cid) for cid in (self.restricted_channel_ids.ids or []))
        param.set_param('oh_discuss_general_restrict.restricted_channel_ids', ids_str)

    @api.model
    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo()
        ids_str = param.get_param('oh_discuss_general_restrict.restricted_channel_ids', default='')
        ids = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
        res.update({
            'restricted_channel_ids': [(6, 0, ids)]
        })
        return res 