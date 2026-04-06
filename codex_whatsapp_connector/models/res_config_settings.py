# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wa_button_models_ids = fields.Many2many(
        'ir.model',
        string="Models with WhatsApp Button",
        help="Only these models' chatters will show the WhatsApp button. Leave empty to show on all models."
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        icp = self.env['ir.config_parameter'].sudo()
        import json
        models_json = icp.get_param('codex_whatsapp_connector.wa_button_models', default='[]')
        try:
            model_names = json.loads(models_json) if models_json else []
        except Exception:
            model_names = []
        model_ids = []
        if model_names:
            Model = self.env['ir.model'].sudo()
            existing = Model.search([('model', 'in', model_names)])
            model_ids = existing.ids
        res.update({
            'wa_button_models_ids': [(6, 0, model_ids)],
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        icp = self.env['ir.config_parameter'].sudo()
        import json
        # Persist models by technical names, not ids
        model_names = []
        if self.wa_button_models_ids:
            model_names = [m.model for m in self.wa_button_models_ids if m.model]
        icp.set_param('codex_whatsapp_connector.wa_button_models', json.dumps(model_names))