from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DiscussChannelWhatsappExt(models.Model):
    _inherit = 'discuss.channel'

    wa_customer_partner_id = fields.Many2one(
        'res.partner', string='WA Customer Partner', index=True
    )
    wa_user_partner_id = fields.Many2one(
        'res.partner', string='WA Agent Partner', index=True
    )
    
    # Persisted flag to identify WhatsApp channels client-side without compute
    is_whatsapp = fields.Boolean(string='Is WhatsApp Channel', default=False, index=True)

    @api.constrains('channel_type', 'wa_customer_partner_id', 'wa_user_partner_id')
    def _check_unique_wa_pair(self):
        for ch in self:
            if ch.channel_type != 'chat':
                continue
            if not ch.wa_customer_partner_id or ch.wa_user_partner_id is False:
                continue
            domain = [
                ('id', '!=', ch.id),
                ('channel_type', '=', 'chat'),
                ('wa_customer_partner_id', '=', ch.wa_customer_partner_id.id),
                ('wa_user_partner_id', '=', ch.wa_user_partner_id.id),
            ]
            if self.search_count(domain):
                raise ValidationError('A WhatsApp chat for this customer/agent pair already exists.')
