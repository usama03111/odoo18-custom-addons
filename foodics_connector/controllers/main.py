# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home
import logging

_logger = logging.getLogger(__name__)

class FoodicsAuthHome(Home):
    
    @http.route()
    def web_login(self, *args, **kw):
        """Function have login features"""
        # Capture Foodics Auth Code from GET request
        if request.httprequest.method == 'GET' and kw.get('code'):
            request.session['foodics_auth_code'] = kw.get('code')

        response = super().web_login(*args, **kw)

        # Exchange Code for Token if User is Logged In
        if request.session.uid:
            code = request.session.pop('foodics_auth_code', False)
            if code:
                try:
                    user = request.env['res.users'].browse(request.session.uid)
                    success = request.env['foodics.auth'].sudo().exchange_code_for_token(user, code)
                    if success:
                        _logger.info("Foodics OAuth: Token exchanged successfully for user %s", user.login)
                    else:
                        _logger.error("Foodics OAuth: Token exchange returned False for user %s", user.login)
                except Exception as e:
                    _logger.error("Foodics OAuth: Verification failed for user %s. Error: %s", 
                                  request.session.uid, e)
            
            # Check if User is connected to Foodics, if not redirect
            else:
                 # Ensure we are not in a loop or handling other auth flows
                 if request.httprequest.method == 'POST' and not kw.get('oauth_provider'):
                    auth_url = request.env['foodics.auth'].sudo().get_authorization_url()
                    if auth_url:
                         _logger.info("Foodics OAuth: Redirecting user %s to Foodics Authorization", )
                         return request.redirect(auth_url)

        return response
