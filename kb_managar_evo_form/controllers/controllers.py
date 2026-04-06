# -*- coding: utf-8 -*-
# from odoo import http


# class KbManagarEvoForm(http.Controller):
#     @http.route('/kb_managar_evo_form/kb_managar_evo_form', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kb_managar_evo_form/kb_managar_evo_form/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kb_managar_evo_form.listing', {
#             'root': '/kb_managar_evo_form/kb_managar_evo_form',
#             'objects': http.request.env['kb_managar_evo_form.kb_managar_evo_form'].search([]),
#         })

#     @http.route('/kb_managar_evo_form/kb_managar_evo_form/objects/<model("kb_managar_evo_form.kb_managar_evo_form"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kb_managar_evo_form.object', {
#             'object': obj
#         })

