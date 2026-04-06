# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import http

import logging
_logger = logging.getLogger(__name__)



class AcsMetaWaba(http.Controller):

    @http.route('/acs/waba/webhooks', type="json", auth="public", methods=['POST','GET'], sitemap=False, csrf=False)
    def acs_waba_webhooks_data(self, **kwargs):
        json_data = request.jsonrequest
        _logger.warning('waba data: %s', json_data)

        mode = json_data.get("hub.mode")
        verify_token = json_data.get("hub.verify_token")
        challenge = json_data.get("hub.challenge")

        # lead = request.env["crm.lead"].sudo().search([('phone','=', str(kwargs.get('number')))], limit=1)
        # _logger.warning('updated lead: %s', lead)
        # if lead:
        #     lead.sudo().write(data)
        return challenge

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: