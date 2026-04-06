# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).


from odoo import fields, models, api
from odoo.exceptions import UserError


class SubPartPaymentConfirm(models.Model):
    _name = "sub.part.payment"
    _description = "Sub Part Payment"
    _order = "index"

    part_amt = fields.Float(string="Amount", required=True)
    installment_ids = fields.Many2many("invoice.installment.line",string="Installments",required=True)

    @api.onchange('installment_ids')
    def _onchange_installment_ids(self):
        return {'domain': {'installment_ids': [('state','=','draft'),('id','in',self.env['account.move'].browse(self._context.get('active_id')).installment_ids.ids)]}}

    @api.constrains('installment_ids')
    def _constrain_installment_ids(self):
        total = sum(self.installment_ids.mapped('amount'))
        if total < self.part_amt:
            raise UserError("Part Amount cannot be greater than the combine seleted installment's amount.")

    def part_payment_confirm(self):
        if self.part_amt > 0:
            res = self.env["account.move"].action_register_payment()
            res["context"].update(
                {
                    "active_ids": self.env.context["active_ids"],
                    "active_id": self.env.context["active_id"],
                    "default_amount": self.part_amt,
                    "line_model": "invoice.installment.line",
                    "default_source_amount": self.part_amt,
                    "default_is_part_payment": True,
                    "default_group_payment": True,
                    "default_part_amt": self.part_amt,
                    "default_installment_lines": str(self.installment_ids.ids),
                    "dont_redirect_to_payments": True,
                }
            )
            return res
