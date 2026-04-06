# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    installment_ids = fields.One2many(
        "invoice.installment.line", "invoice_id", "Installments"
    )
    tenure = fields.Integer(
        string="Tenure (months)", states={"draft": [("readonly", False)]}
    )
    installment_amt = fields.Float(
        string="Installment Amount", states={"draft": [("readonly", False)]}
    )
    compute_installment = fields.Char(string="Compute")
    part_payment = fields.Char(string="Part Payment")
    down_payment_amt = fields.Float(
        string="Down Payment",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    first_installment_date = fields.Date(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    payable_amt = fields.Float(
        string="Payable Amount",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    tenure_amt = fields.Float(
        compute="_compute_tenure_amt", string="Tenure Amount"
    )

    tenure_plan = fields.Selection(
        [("quater", "Quaterly"), ("month", "Monthly"), ("days", "Days")]
    )

    enable_installment = fields.Boolean(
        related="company_id.enable_installments"
    )
    single_invoice_installment = fields.Boolean()
    multiple_invoice_installment = fields.Boolean()
    sale_installment_line_id = fields.Many2one(
        "sale.installment.line",
        string="Sale Installment Line",
        help="Installment line on the sale order that generated this invoice.",
    )

    paid_amount_summary = fields.Monetary("Paid Amount", readonly=True, compute="_compute_installment_amount_summary")
    balance_amount_summary = fields.Monetary("Balance Amount", readonly=True, compute="_compute_installment_amount_summary")

    check_invoice_type = fields.Char(string='',compute='_compute_single_or_multiple')

    last_installment_reminder_date = fields.Date(
        string="Last Installment Reminder Date",
        help="Technical field used to avoid sending reminder emails too often "
        "for installment invoices.",
    )

    def _compute_invoice_date_due(self):
        super()._compute_invoice_date_due()
        for move in self:
            sale_line = move.sale_installment_line_id
            sale = sale_line.sale_id if sale_line else False
            plan = sale.installment_plans_id if sale else False
            if (
                sale
                and sale.multiple_invoice_installment
                and plan
                and plan.installment_due_days
            ):
                reference_date = move.invoice_date or move.date or fields.Date.context_today(move)
                move.invoice_date_due = reference_date + relativedelta(
                    days=plan.installment_due_days
                )


    # ============================
    #     ONCHANGE METHODS
    # ============================


    def _compute_single_or_multiple(self):
        report_id = self.env.ref('payment_installment_kanak.action_invoice_report_installments')

        if self.multiple_invoice_installment:
            self.check_invoice_type = "multiple"
            report_id.unlink_action()



        else:
            self.check_invoice_type = "single"

            report_id.create_action()


    @api.onchange("installment_amt")
    def _onchange_installment_amt_tenure(self):
        if self.installment_amt:
            self.tenure = round(self.amount_residual / self.installment_amt)


    @api.onchange("tenure")
    def _onchange_tenure(self):
        if self.tenure:
            self.installment_amt = round(self.amount_residual / self.tenure)

    def onchange(self, values, field_name, field_onchange):
        return super(
            AccountMove, self.with_context(recursive_onchanges=False)
        ).onchange(values, field_name, field_onchange)

    # ============================
    #     PDF REPORT METHODS
    # ============================

    def get_payment_schedule_data(self):
        ten_plan = ""
        if self.tenure_plan == "quater":
            ten_plan = "Quaterly"
        elif self.tenure_plan == "days":
            ten_plan = "Days"
        else:
            ten_plan = "Monthly"
        tot_instal = self.tenure
        tot_price = self.amount_total

        disc = 0
        for rec in self.invoice_line_ids:
            if rec.discount:
                disc += round((rec.price_subtotal * rec.discount) / 100, 2)

        balance = round(tot_price - disc, 2)
        values = []
        instal_state = ""
        for rec in self.installment_ids:
            amount_paid = 0

            if rec.is_installment:
                if rec.state == "draft":
                    if rec.register_payment_date and rec.register_payment_date < fields.Date.today():
                        instal_state = 'overdue'
                    else:
                        if rec.amount < self.installment_amt:
                            instal_state = 'partial'
                        else:
                            instal_state = "due"
                else:
                    instal_state = "paid"

                if instal_state == "paid":
                    amount_paid = rec.amount
                elif instal_state == "partial":
                    amount_paid = self.installment_amt - rec.amount
            else:
                if rec.state == "draft":
                    if rec.register_payment_date and rec.register_payment_date < fields.Date.today():
                        instal_state = 'overdue'
                    else:
                        if rec.amount < rec.sinst_line_id.amount:
                            instal_state = 'partial'
                        else:
                            instal_state = "due"
                else:
                    instal_state = "paid"

                if instal_state == "paid":
                    amount_paid = rec.amount
                elif instal_state == "partial":
                    amount_paid = rec.sinst_line_id.amount - rec.amount




            values.append(
                {
                    "description": rec.description,
                    "amount": rec.amount,
                    "due_date": rec.payment_date,
                    "status": instal_state,
                    "medium": rec.journal_id.name,
                    "register_date": rec.register_payment_date,
                    "is_installment": True if rec.is_installment else False,
                    "amount_paid": amount_paid
                }
            )

        value = sorted(values, key=lambda date: date["due_date"])

        over_amt = 0
        for line in self.installment_ids:
            if line.state == 'paid' and line.register_payment_date:
                if line.payment_date < line.register_payment_date:
                    over_amt += line.amount


        data = {
            "tenure_plan": ten_plan,
            "total_installment": tot_instal,
            "total_price": tot_price,
            "discount": disc,
            "amount_paid_to_date": self.paid_amount_summary,
            "balance": self.balance_amount_summary,
            "overdue_amount": over_amt,
            "values": value,
            "status": True if self.payment_state != 'paid' else False,
        }

        return data

    def get_product_names(self):
        names = []
        for line in self.invoice_line_ids:
            names.append(line.product_id.name)

        name = list(set(names))
        return name

    # ============================
    #     COMPUTED METHODS
    # ============================

    @api.depends('installment_ids.state')
    def _compute_installment_amount_summary(self):
        for rec in self:
            amount = 0
            total_amount = 0
            for line in rec.installment_ids:
                total_amount += line.amount
                if line.state == 'draft':
                    amount += line.amount
                    

            rec.paid_amount_summary = total_amount - amount
            rec.balance_amount_summary = amount

    @api.depends("amount_total")
    def _compute_tenure_amt(self):
        for record in self:
            record.tenure_amt = record.amount_total

class account_payment(models.Model):
    _inherit = "account.payment"

    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        ctx = self.env.context
        if ctx.get("default_amount"):
            rec.update({"amount": ctx["default_amount"]})
        return rec

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        total = super(account_payment, self)._compute_payment_amount(
            invoices, currency, journal, date
        )
        ctx = self.env.context
        if ctx.get("default_amount"):
            return ctx["default_amount"]
        return total

    def action_post(self):
        res = super(account_payment, self).action_post()
        ctx = self.env.context
        if ctx.get("line_model", False) and ctx.get("line_id", False):
            line = self.env[ctx["line_model"]].browse(ctx["line_id"])
            line.journal_id = self.journal_id.id
            line.register_payment_date = self.date
            line.state = "paid"
            if line.sinst_line_id:
                line.sinst_line_id.state = "paid"
        return res


class SaleInstallmentLine(models.Model):
    _name = "sale.installment.line"
    _description = "Sale Installment Line"
    _order = "payment_date"
    _rec_name = "description"

    amount = fields.Float()
    index = fields.Integer(string="#No")
    sale_id = fields.Many2one("sale.order", "Sale Order", ondelete="cascade")
    payment_date = fields.Date()
    description = fields.Char()
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("paid", "Paid")],
        default="draft",
        string="Status",
    )
    is_installment = fields.Boolean()


class InvoiceInstallmentLine(models.Model):
    _name = "invoice.installment.line"
    _description = "Invoice Installment Line"
    _order = "payment_date"
    _rec_name = "description"

    amount = fields.Float()
    index = fields.Integer(string="#No")
    invoice_id = fields.Many2one("account.move", "Invoice")
    sale_id = fields.Many2one("sale.order", "Sale Order")
    payment_date = fields.Date()
    description = fields.Char()
    paid = fields.Boolean()
    sinst_line_id = fields.Many2one(
        "sale.installment.line", "Sale Installment Line"
    )
    state = fields.Selection(
        [("draft", "Due"), ("paid", "Paid")],
        default="draft",
        string="Status",
    )

    journal_id = fields.Many2one("account.journal")
    register_payment_date = fields.Date()
    is_installment = fields.Boolean()

    def make_payment(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No invoice linked to this installment."))
        if self.invoice_id.state != "posted":
            raise UserError(_("You can only pay installments of posted invoices."))

        action = self.invoice_id.action_register_payment()
        context = dict(action.get("context", {}))
        context.update(
            {
                "active_model": "account.move",
                "active_ids": self.invoice_id.ids,
                "active_id": self.invoice_id.id,
                "default_amount": self.amount,
                "line_id": self.id,
                "line_model": "invoice.installment.line",
                "default_is_installment_payment": True,
                "dont_redirect_to_payments": True,
                "default_group_payment": True,
            }
        )
        action["context"] = context
        return action

    # @api.model
    # def installment_reminder(self):
    #     tommorow = fields.Datetime.today() + relativedelta(days=1)
    #     day_after_tommorow = fields.Datetime.today() + relativedelta(days=2)
    #     records = self.search(
    #         [
    #             ("invoice_id.state", "=", "posted"),
    #             "|",
    #             ("payment_date", "=", tommorow),
    #             ("payment_date", "=", day_after_tommorow),
    #         ]
    #     )
    #
    #     for rec in records:
    #         template = self.env.ref(
    #             "payment_installment_kanak.mail_template_installment_reminder"
    #         )
    #         template.send_mail(
    #             rec.id,
    #             force_send=True,
    #             email_values={"email_from": self.env.user.partner_id.email},
    #         )
