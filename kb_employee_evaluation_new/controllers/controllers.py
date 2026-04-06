# -*- coding: utf-8 -*-
# from odoo import http


# class KbEmployeeEvaluation(http.Controller):
#     @http.route('/kb_employee_evaluation/kb_employee_evaluation', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kb_employee_evaluation/kb_employee_evaluation/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kb_employee_evaluation.listing', {
#             'root': '/kb_employee_evaluation/kb_employee_evaluation',
#             'objects': http.request.env['kb_employee_evaluation.kb_employee_evaluation'].search([]),
#         })

#     @http.route('/kb_employee_evaluation/kb_employee_evaluation/objects/<model("kb_employee_evaluation.kb_employee_evaluation"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kb_employee_evaluation.object', {
#             'object': obj
#         })

