from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_score = fields.Integer(string='Loyalty Score', default=0, help="Customer loyalty score for POS discounts.")

    # The _load_pos_data_fields function is used to load custom fields into the(POS).
    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['loyalty_score']
        return params
