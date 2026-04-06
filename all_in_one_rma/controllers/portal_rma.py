from odoo import http
from odoo.http import request

class PortalRMA(http.Controller):

    @http.route(['/my/rma'], type='http', auth="user", website=True)
    def portal_rma(self, **kw):
        rmas = request.env['rma.request'].sudo().search([('customer_id','=',request.env.user.partner_id.id)])
        return request.render('all_in_one_rma.portal_rma_list', {'rmas': rmas})

    @http.route(['/my/rma/create'], type='http', auth="user", website=True)
    def portal_rma_create(self, **kw):
        orders = request.env['sale.order'].sudo().search([('partner_id','=',request.env.user.partner_id.id)])
        return request.render('all_in_one_rma.portal_rma_create', {'orders': orders})

    @http.route(['/my/rma/submit'], type='http', auth="user", website=True, methods=['POST'])
    def portal_rma_submit(self, **kw):
        order_id = int(kw.get('order_id'))
        order_line_ids = [int(i) for i in kw.getlist('order_line_ids')]
        reason = kw.get('reason')
        rma_type = kw.get('type')
        request.env['rma.request'].sudo().create({
            'order_id': order_id,
            'order_line_ids': [(6,0,order_line_ids)],
            'reason': reason,
            'type': rma_type,
            'status': 'submitted',
        })
        return request.redirect('/my/rma')
