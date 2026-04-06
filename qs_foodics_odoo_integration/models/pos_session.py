from odoo import fields, models, api
from datetime import datetime
now = datetime.now()


class AccountMoveTrans(models.Model):
    _inherit = 'account.journal'

    internal_pos_move = fields.Boolean(string="Internal Pos Move")
    payment_mehtod = fields.Many2one('pos.payment.method', string="Payment Method")
    pos_branch = fields.Many2one('pos.config', string="POS Branch ")



class PosPaymentTrans(models.Model):
    _inherit = 'pos.payment.method'
    _description = 'Pos Payment Add Transactions'

    internal_trans = fields.Boolean(string="Internal Transaction")



class PosSession(models.Model):
    _inherit = 'pos.session'
    def create_move_cust(self):
        x = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_amount = 0
        untaxed_amount = 0
        data = []
        payment_ids = []
        payment_data=[]
        get_payment = self.env['pos.payment'].search([('session_id','=',self.id)]).payment_method_id
        for pa in get_payment:
            payment_ids.append(pa.id)
        for payment in payment_ids:
            total = 0
            get_orderes =self.env['pos.payment'].search([('session_id', '=', self.id),
                                                           ('payment_method_id','=',payment)])
            get_account_payment = self.env['pos.payment.method'].search([('id','=',payment)])
            for order in get_orderes:
                total = order.amount + total
            total_amount = total_amount + total
            # data.append([get_account_payment.name,total, get_account_payment.receivable_account_id.id])
            get_tax = total / 1.15
            get_tot = total - get_tax
            untaxed_amount = get_tot + untaxed_amount
            data.append((0,0,{
                'account_id': get_account_payment.receivable_account_id.id,
                'debit': total,
                'name': get_account_payment.name,
                'credit': 0,}))
            payment_journal = self.env['account.payment'].create({
                'payment_type': 'inbound',
                'amount':total,
                'date': x,
                'ref': "Combine " + get_account_payment.name + " POS payments from "+ self.name,
                'journal_id': get_account_payment.journal_id.id,
            })
            payment_journal.action_post()
            if get_account_payment.internal_trans:
                get_journal = self.env['account.journal'].search([('internal_pos_move','=', True),
                                                                  ('payment_mehtod','=',get_account_payment.id),
                                                                  ('pos_branch','=',self.config_id.id)], limit=1)
                if get_journal:
                    payment_tans = self.env['account.payment'].create({
                        'is_internal_transfer': True,
                        'payment_type': 'outbound',
                        'amount': total,
                        'date': x,
                        'ref': "Combine " + get_account_payment.name + " POS payments from " + self.name,
                        'journal_id': get_account_payment.journal_id.id,
                        'destination_journal_id': get_journal.id,
                    })
                    payment_tans.action_post()

        get_tax = total_amount / 1.15
        totaa = total_amount - get_tax
        data.append((0,0,{
            'account_id': 2388,
            'debit': 0,
            'name': "TAX",
            'credit': untaxed_amount,}))
        if self.config_id.account_analytic_id:
            data.append((0,0, {
                'account_id': 2515,
                'debit': 0,
                'name': "Sales",
                'credit': get_tax,
                'analytic_distribution': {self.config_id.account_analytic_id.id: 100},
                }))
        else:
            data.append((0,0, {
                'account_id': 2515,
                'debit': 0,
                'name': "Sales",
                'credit': get_tax,
                }))
        journal = self.env['account.move'].create({
            'name': self.name,
            'date': x,
            'journal_id': 6,
            'invoice_line_ids':data,
        })
        self.move_id = journal.id
        self.move_id.action_post()
        self.state = 'closed'
        self.stop_at = now
