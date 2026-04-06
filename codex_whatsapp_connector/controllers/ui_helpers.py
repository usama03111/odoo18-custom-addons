from odoo import http
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)


class WhatsAppUIController(http.Controller):
    """Lightweight controller for UI-related helper routes (button visibility, WA channels)."""

    @http.route('/whatsapp/allowed_models', type='json', auth='user')
    def allowed_models(self):
        """Return the list of technical model names where the WhatsApp button should be shown."""
        try:
            icp = request.env['ir.config_parameter'].sudo()
            models_json = icp.get_param('codex_whatsapp_connector.wa_button_models', default='[]')
            try:
                model_names = json.loads(models_json) if models_json else []
            except Exception:
                model_names = []
            return {"models": model_names}
        except Exception as e:
            _logger.error(f"allowed_models error: {str(e)}")
            return {"models": []}

    @http.route('/whatsapp/is_wa_channel', type='json', auth='user')
    def is_wa_channel(self, channel_id):
        """Tell the frontend if the given Discuss channel is a WhatsApp channel."""
        try:
            if not channel_id:
                return {"is_wa": False}
            channel = request.env['discuss.channel'].sudo().browse(int(channel_id))
            if not channel.exists():
                return {"is_wa": False}
            is_wa = bool(channel.is_whatsapp or channel.wa_customer_partner_id)
            return {"is_wa": is_wa}
        except Exception as e:
            _logger.error(f"is_wa_channel error: {str(e)}")
            return {"is_wa": False}
