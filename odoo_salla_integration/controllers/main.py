# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   "License URL : <https://store.webkul.com/license.html/>"
#
##########################################################################

from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class OdooSallaConnector(http.Controller):

	@http.route('/salla/authenticate', type='http', auth='public')
	def odoo_salla_connector(self, *args, **kwargs):
		try:
			url = self.salla_get_multichannel_url()
			return_key = kwargs.get('state')
			if return_key:
				connection = request.env['multi.channel.sale'].search([('salla_verification_key','=',return_key)], limit=1)
				if not connection:
					_logger.error(
						f'Authentication Failed, there is no multichannel instance with verification key: [{return_key}] in your odoo')
					return request.redirect(url)
				if kwargs.get('error'):
					connection.write({'state': 'error'})
					_logger.error('Error: %r', kwargs.get('error'))
				else:
					get = connection.create_salla_connection(kwargs)
					if get:
						url = self.salla_get_multichannel_url(connection.id)
					else:
						get = connection.write({'state': 'error'})
		except Exception as e:
			_logger.error("Error Found While Generating Access Token %r", str(e))
		return request.redirect(url)


	def salla_get_multichannel_url(self, instance_id = False):
		action_id = request.env.ref(
				'odoo_multi_channel_sale.action_multi_channel_view').id
		if instance_id:
			return  "/web#id={}&action={}&model=multi.channel.sale&view_type=form".format(
					instance_id, action_id)
		else:
			return "/web#action={}&model=multi.channel.sale".format(action_id)
