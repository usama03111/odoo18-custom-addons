# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import base64


class SaleOrder(models.Model):
    _inherit = "sale.order"

    installment_ids = fields.One2many(
        "sale.installment.line", "sale_id", "Installments"
    )

    down_payment_amt_ids = fields.One2many(
        "down.payment",
        "sale_order_id",
        string="Down Payment",

    )

    first_installment_date = fields.Date(
        string="First Installment Date",

    )

    installment_amt = fields.Float(
        string="Installment Amount",

    )

    payable_amt = fields.Float(
        string="Payable Amount",
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )

    tenure = fields.Integer(
        string="Tenure (months)",
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )

    tenure_amt = fields.Float(
        compute="_compute_tenure_amt", string="Total Amount"
    )

    tenure_plan = fields.Selection(
        [("quater", "Quaterly"), ("month", "Monthly"), ("days", "Days")], default="month"
    )

    single_invoice_installment = fields.Boolean()

    multiple_invoice_installment = fields.Boolean()

    days_before_invoice = fields.Integer()
    installment_reminder_days = fields.Integer(
        string="Installment Reminder After (Days)",
        help="Number of days after the installment due date to send a payment reminder "
        "email for posted but unpaid installment invoices.",
    )
    
    installment_plans_id = fields.Many2one(
        "account.payment.term",
        domain="[('is_plan','=',True)]",
        tracking=True,
    )
    
    next_invoice_date = fields.Date()
    
    installment_last_date = fields.Date()
    
    mul_inv_first_created = fields.Boolean(compute="_compute_date_flag")
    
    enable_installment = fields.Boolean(
        related="company_id.enable_installments"
    )

    down_payment_amount = fields.Float()

    # ============================
    #     COMPUTED METHODS
    # ============================

    @api.depends("amount_total")
    def _compute_tenure_amt(self):
        for record in self:
            record.tenure_amt = record.amount_total

    def _get_next_installment_line(self):
        """Return the next draft installment line (prioritizing earlier payment dates)."""
        self.ensure_one()
        draft_lines = self.installment_ids.filtered(lambda l: l.state == "draft")
        if not draft_lines:
            return self.env["sale.installment.line"]
        return draft_lines.sorted(key=lambda l: l.payment_date or fields.Date.today())[0]

    def _compute_date_flag(self):
        for rec in self:
            if rec.installment_plans_id:
                if self.single_invoice_installment:
                    rec.mul_inv_first_created = True
                elif self.multiple_invoice_installment:
                    if rec.delivery_status != "pending":
                        # Check if first installment (down payment or first regular) has been invoiced
                        # Get the first installment in draft state (prioritizes down payments)
                        draft_installments = rec.installment_ids.filtered(
                            lambda r: r.state == "draft"
                        )
                        if draft_installments:
                            # There are still draft installments, so first invoice not yet created
                            rec.mul_inv_first_created = True
                        else:
                            # All installments are posted or paid, so first invoice already created
                            rec.mul_inv_first_created = False
                    else:
                        rec.mul_inv_first_created = False
                else:
                    self.mul_inv_first_created = False
            else:
                rec.mul_inv_first_created = True


    # ============================
    #     ONCHANGE METHODS
    # ============================

    @api.onchange("down_payment_amt_ids")
    def _onchange_down_payment_amt_ids_amount(self):
        total_amt = sum(self.down_payment_amt_ids.mapped("amount"))
        if total_amt > self.payable_amt:
            raise ValidationError(
                "Amount cannot be greater than Payable Amount"
            )

    @api.onchange("installment_amt")
    def _onchange_installment_amt_tenure(self):
        if self.installment_amt:
            self.with_context(
                {"installment_amt": self.installment_amt}
            ).tenure = round(self.payable_amt / self.installment_amt)

    @api.onchange("tenure", "down_payment_amt_ids", "tenure_plan")
    def _onchange_tenure(self):
        if self.tenure:
            self.installment_amt = round(self.payable_amt / self.tenure)

    def onchange(self, values, field_name, field_onchange):
        return super(
            SaleOrder, self.with_context(recursive_onchanges=False)
        ).onchange(values, field_name, field_onchange)

    @api.onchange("down_payment_amt_ids", "order_line")
    def _onchange_down_payment_amt_ids(self):
        dwn_pymnt = 0
        for payment in self.down_payment_amt_ids:
            dwn_pymnt += payment.amount
        if self.amount_total:
            self.payable_amt = self.amount_total - dwn_pymnt

    def _recompute_down_payment_totals(self):
        for order in self:
            previous_tenure = order.tenure
            previous_installment = order.installment_amt
            total_down = sum(order.down_payment_amt_ids.mapped("amount"))
            base_amount = order.tenure_amt or order.amount_total or 0.0
            order.payable_amt = max(base_amount - total_down, 0.0)
            tenure_to_use = order.tenure
            if not tenure_to_use and order.installment_plans_id:
                tenure_to_use = order._get_plan_tenure_months(order.installment_plans_id)
                if tenure_to_use:
                    order.tenure = tenure_to_use
            if tenure_to_use:
                order.installment_amt = (
                    order.payable_amt / tenure_to_use if tenure_to_use else 0.0
                )
            else:
                # Preserve previous installment amount if tenure is still not defined
                order.installment_amt = previous_installment
                if previous_tenure:
                    order.tenure = previous_tenure

    def _get_plan_tenure_months(self, plan):
        self.ensure_one()
        months = 0
        for line in plan.line_ids:
            if line.value == "balance":
                period = getattr(line, "period", "month") or "month"
                if period == "days":
                    # For days period, use days field value as tenure
                    days_value = getattr(line, "days", 0) or 0
                    months = days_value  # Return days value as tenure
                else:
                    months = getattr(line, "months", 0) or 0
                    if not months and hasattr(line, "nb_days"):
                        nb_days = getattr(line, "nb_days", 0) or 0
                        months = max(1, nb_days // 30) if nb_days else 0
                break
        return months

    def _prepare_installment_plan_values(self):
        self.ensure_one()
        plan = self.installment_plans_id
        if not plan:
            return {}

        base_amount = self.tenure_amt or self.amount_total or 0.0
        base_date = self.date_order or fields.Date.context_today(self)

        down_payment_values = []
        total_advance_amt = 0.0
        tenure = 0
        tenure_plan = self.tenure_plan or "month"
        first_installment_date = self.first_installment_date

        for line in plan.line_ids:
            months = getattr(line, "months", 0) or 0
            nb_days = getattr(line, "nb_days", 0) or 0
            due_date = base_date
            if months:
                due_date = due_date + relativedelta(months=months)
            elif nb_days:
                due_date = due_date + relativedelta(days=nb_days)

            if line.value != "balance":
                dwn_amt = 0.0
                if line.value == "fixed":
                    dwn_amt = line.value_amount
                elif line.value == "percent":
                    dwn_amt = (base_amount * line.value_amount) / 100.0

                down_payment_values.append(
                    (
                        0,
                        0,
                        {
                            "description": line.description or _("Advance payment"),
                            "due_date": self.date_order + relativedelta(months=line.months),
                            # "due_date": due_date,
                            "amount": dwn_amt,
                        },
                    )
                )
                total_advance_amt += dwn_amt
            else:
                tenure_plan = getattr(line, "period", "month") or "month"
                start_base = line.start_date or base_date
                
                if tenure_plan == "days":
                    # For days period, days field represents BOTH:
                    # 1. The number of installments to create
                    # 2. The interval (in days) between each installment
                    days_value = getattr(line, "days", 0) or 0
                    if not days_value:
                        raise UserError(
                            _("The days field for the balance plan type cannot be equal to 0 when period is Days.")
                        )
                    tenure = days_value  # Number of installments = days field value
                    first_installment_date = start_base + relativedelta(days=1)  # First installment is 1 day after start
                else:
                    # For month/quater period, use months
                    computed_months = months
                    if not computed_months and nb_days:
                        computed_months = max(1, nb_days // 30)
                    if not computed_months:
                        raise UserError(
                            _("The months for the balance plan type cannot be equal to 0.")
                        )
                    tenure = computed_months
                    first_installment_date = start_base + relativedelta(months=1)

        values = {
            "payment_term_id": plan.id,
            "tenure_plan": tenure_plan,
        }
        if down_payment_values or self.down_payment_amt_ids:
            values["down_payment_amt_ids"] = [(5, 0, 0)]
            if down_payment_values:
                values["down_payment_amt_ids"].extend(down_payment_values)
        payable_amt = max(base_amount - total_advance_amt, 0.0)
        values["payable_amt"] = payable_amt
        if tenure:
            values["tenure"] = tenure
            values["installment_amt"] = payable_amt / tenure if tenure else 0.0
        if first_installment_date:
            values["first_installment_date"] = first_installment_date
        return values

    @api.onchange("installment_plans_id")
    def _onchange_installment_plans_id(self):
        if not self.installment_plans_id:
            return
        values = self._prepare_installment_plan_values()
        for field_name, value in values.items():
            if field_name == "down_payment_amt_ids":
                self.down_payment_amt_ids = value
            else:
                setattr(self, field_name, value)
        
        # Ensure tenure is set for days period
        if self.installment_plans_id and self.tenure_plan == "days" and not self.tenure:
            balance_line = self.installment_plans_id.line_ids.filtered(lambda l: l.value == "balance")
            if balance_line:
                days_value = getattr(balance_line[0], "days", 0) or 0
                if days_value:
                    self.tenure = days_value
            
    
    # ============================
    #     REPORT METHODS
    # ============================

    def get_product_names(self):
        names = []
        for order in self.order_line:
            names.append(order.product_id.name)

        name = list(set(names))
        return name

    # For Report
    def get_payment_schedule_data(self):
        ten_plan = ""
        if self.tenure_plan == "quater":
            ten_plan = "Quaterly"
        elif self.tenure_plan == "days":
            ten_plan = "Days"
        else:
            ten_plan = "Monthly"
        tot_instal = self.tenure
        tot_price = self.amount_undiscounted

        disc = 0
        for rec in self.order_line:
            if rec.discount:
                disc += round((rec.price_subtotal * rec.discount) / 100, 2)

        balance = round(tot_price - disc, 2)
        values = []
        instal_state = ""
        for rec in self.installment_ids:
            if rec.state == "draft":
                instal_state = "Due"
            elif rec.state == "posted":
                instal_state = "Posted"
            else:
                instal_state = "Paid"
            values.append(
                {
                    "description": rec.description,
                    "amount": rec.amount,
                    "due_date": rec.payment_date,
                    "status": instal_state,
                }
            )

        value = sorted(values, key=lambda date: date["due_date"])

        amt_paid_date = 0
        over_amt = 0
        for line in values:
            if line["status"] == "Paid":
                amt_paid_date += line["amount"]
            if (
                line["status"] == "Due"
                and line["due_date"] < fields.date.today()
                and "Installment" in line["description"]
            ):
                over_amt += line["amount"]

        data = {
            "tenure_plan": ten_plan,
            "total_installment": tot_instal,
            "total_price": tot_price,
            "discount": disc,
            "amount_paid_to_date": amt_paid_date,
            "balance": balance,
            "overdue_amount": over_amt,
            "values": value,
        }

        return data

    # ============================
    #  OTHER OBJECT TYPE METHODS
    # ============================

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ["cancel", "sent"])
        orders.installment_ids.unlink()

        res = super(SaleOrder, self).action_draft()
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            # Ensure down_payment_amt_ids are created if installment_plans_id is set
            if order.installment_plans_id and not order.down_payment_amt_ids:
                down_payment_values = []
                total_advance_amt = 0
                for line in order.installment_plans_id.line_ids:
                    if line.value != "balance":
                        dwn_amt = 0
                        if line.value == "fixed":
                            dwn_amt = line.value_amount
                        elif line.value == "percent":
                            dwn_amt = (order.tenure_amt * line.value_amount) / 100

                        # Calculate due date - use months if available, otherwise use nb_days or default to today
                        months = getattr(line, 'months', 0) or 0
                        due_date = order.date_order or fields.Date.today()
                        if months:
                            due_date = due_date + relativedelta(months=months)
                        elif hasattr(line, 'nb_days') and line.nb_days:
                            due_date = due_date + relativedelta(days=line.nb_days)

                        down_payment_values.append(
                            (0, 0, {
                                "description": line.description or "Advance payment",
                                "due_date": due_date,
                                "amount": dwn_amt,
                            })
                        )
                        total_advance_amt += dwn_amt
                    else:
                        # Set tenure and first_installment_date if not set
                        if not order.tenure:
                            tenure_plan = getattr(line, 'period', 'month') or 'month'
                            order.tenure_plan = tenure_plan
                            
                            if tenure_plan == 'days':
                                # For days period, days field represents BOTH:
                                # 1. The number of installments to create
                                # 2. The interval (in days) between each installment
                                days_value = getattr(line, 'days', 0) or 0
                                if days_value:
                                    order.tenure = days_value  # Number of installments = days field value
                                    start_base = line.start_date or order.date_order or fields.Date.today()
                                    order.first_installment_date = start_base + relativedelta(days=1)  # First installment is 1 day after start
                            else:
                                # For month/quater period, use months
                                months = getattr(line, 'months', 0) or 0
                                if months == 0:
                                    # Try to get from nb_days and convert to months (approximate)
                                    if hasattr(line, 'nb_days') and line.nb_days:
                                        months = max(1, line.nb_days // 30)  # Approximate months
                                if months:
                                    order.tenure = months
                                    start_base = line.start_date or order.date_order or fields.Date.today()
                                    order.first_installment_date = start_base + relativedelta(months=1)

                if down_payment_values:
                    order.down_payment_amt_ids = down_payment_values
                    if not order.payable_amt:
                        order.payable_amt = order.tenure_amt - total_advance_amt
                    if not order.installment_amt and order.tenure and order.tenure > 0:
                        order.installment_amt = order.payable_amt / order.tenure

            amount_total = order.payable_amt
            tenure = order.tenure
            installment_ids = []
            today_date = fields.date.today()

            index = 1
            factor = 1
            days_factor = 0
            if order.tenure_plan == "quater":
                factor = 3
            elif order.tenure_plan == "days":
                # For days period, we don't need days_factor for initial date calculation
                # Installments will be created with 1 day interval
                days_factor = 1  # Set to 1 for consecutive days
            if order.first_installment_date:
                if order.tenure_plan == "days":
                    # For days period, today_date is not used in the same way
                    today_date = order.first_installment_date - relativedelta(days=1)
                else:
                    today_date = order.first_installment_date - relativedelta(months=factor)
            if order.down_payment_amt_ids:
                total_amt = 0
                for payment in order.down_payment_amt_ids:
                    installment_ids.append(
                        [
                            0,
                            0,
                            {
                                "amount": payment.amount,
                                "payment_date": payment.due_date,
                                "description": payment.description,
                            },
                        ]
                    )
                    index += 1
                    total_amt += payment.amount

            instal_factor = 1
            # Create installments if installment_amt is set OR if installment_plans_id is set and we have tenure
            if order.installment_amt or (order.installment_plans_id and order.tenure and order.tenure > 0):
                # Ensure installment_amt is set if missing
                if not order.installment_amt and order.tenure and order.tenure > 0 and order.payable_amt:
                    order.installment_amt = order.payable_amt / order.tenure

                payment_date = order.first_installment_date or today_date
                amount = order.installment_amt or 0
                # Ensure tenure is set - use order.tenure directly
                if not tenure:
                    tenure = order.tenure or 0
                # For days period, make sure we have the correct tenure value
                if order.tenure_plan == "days" and not tenure and order.installment_plans_id:
                    balance_line = order.installment_plans_id.line_ids.filtered(lambda l: l.value == "balance")
                    if balance_line:
                        tenure = getattr(balance_line[0], "days", 0) or 0
                        if tenure:
                            order.tenure = tenure
                while tenure > 0:
                    if amount_total < 0.0:
                        raise UserError(
                            _(
                                "Installment Amount Or Number Of Installment Mismatch Error."
                            )
                        )
                    if tenure == 1:
                        amount = order.tenure_amt - total_amt
                    installment_ids.append(
                        [
                            0,
                            0,
                            {
                                "amount": amount,
                                "payment_date": payment_date,
                                "description": "%s installment"
                                % instal_factor,
                                "is_installment": True,
                            },
                        ]
                    )
                    total_amt += amount
                    index += 1
                    tenure -= 1
                    factor = 1
                    instal_factor += 1
                    if order.tenure_plan == "quater":
                        factor = 3
                        payment_date += relativedelta(months=factor)
                    elif order.tenure_plan == "days":
                        # For days period, create installments with 1 day interval (consecutive days)
                        # The days field value represents the number of installments, not the interval
                        payment_date += relativedelta(days=1)
                    else:
                        payment_date += relativedelta(months=factor)
                    amount_total -= order.installment_amt
            ind = 1
            if installment_ids:
                order.installment_ids = installment_ids
            for rec in order.installment_ids:
                rec.index = ind
                ind += 1

            if order.installment_plans_id:
                if (
                    self.env.company.installment_invoice_settings
                    == "single_invoice"
                ):
                    order.single_invoice_installment = True
                    order.multiple_invoice_installment = False
                    order.days_before_invoice = 0
                    order.installment_last_date = False
                else:
                    order.single_invoice_installment = False
                    order.multiple_invoice_installment = True
                    order.days_before_invoice = (
                        self.env.company.days_before_invoice
                    )
                    if order.tenure_plan == "month":
                        order.installment_last_date = (
                            order.first_installment_date
                            + relativedelta(months=order.tenure)
                        )
                    elif order.tenure_plan == "days":
                        # For days period, calculate last date: first_date + (tenure - 1) days
                        # tenure = number of installments, interval = 1 day between each
                        # Last installment date = first_date + (number_of_installments - 1) days
                        order.installment_last_date = (
                            order.first_installment_date
                            + relativedelta(days=order.tenure - 1)
                        )
                    else:
                        order.installment_last_date = (
                            order.first_installment_date
                            + relativedelta(months=3 * order.tenure)
                        )
        return res

    # ============================
    #     CRON REMINDER METHOD
    # ============================

    @api.model
    def installment_overdue_reminder(self):
        """Send reminder emails for posted installments that are not yet paid.

        Uses `installment_reminder_days` on the sale order to determine how many days
        after the installment due date (invoice due date) the reminder should be sent.
        """
        today = fields.Date.today()

        # Only consider orders using multiple invoice installments with a positive reminder delay
        orders = self.search(
            [
                ("multiple_invoice_installment", "=", True),
                ("installment_reminder_days", ">", 0),
            ]
        )

        if not orders:
            return

        template = self.env.ref(
            "payment_installment_kanak.mail_template_multiple_installment_overdue",
            raise_if_not_found=False,
        )
        if not template:
            return

        Move = self.env["account.move"]

        for order in orders:
            days = order.installment_reminder_days
            for line in order.installment_ids.filtered(lambda l: l.state == "posted"):
                # Find the invoice created for this installment line
                invoice = Move.search(
                    [
                        ("sale_installment_line_id", "=", line.id),
                        ("state", "=", "posted"),
                    ],
                    limit=1,
                )
                if not invoice or invoice.payment_state == "paid":
                    continue

                # Send reminder every N days after invoice creation, while unpaid.
                # Use last_installment_reminder_date on the invoice to avoid duplicates.
                invoice_date = invoice.invoice_date or invoice.date
                if not invoice_date:
                    continue

                days_since = (today - invoice_date).days
                if days_since < days:
                    continue

                # If we've already sent a reminder recently, respect the interval.
                if invoice.last_installment_reminder_date:
                    gap = (today - invoice.last_installment_reminder_date).days
                    if gap < days:
                        continue

                # Also require that we've passed at least one full interval from creation.
                if days_since % days != 0:
                    continue
                print(f"these mail is sent to these invoice {invoice.name} and invoice date is {invoice_date} and invoice sent after {self.installment_reminder_days}")
                # Send email to customer with remaining amount
                email_from = (
                    order.user_id.partner_id.email
                    or self.env.user.partner_id.email
                )
                template.with_context(email_from=email_from).send_mail(
                    invoice.id,
                    force_send=True,
                )
                # Log a simple note in the invoice chatter
                invoice.message_post(
                    body=_(
                        "Installment payment reminder email sent. Outstanding amount: %s"
                    )
                    % invoice.currency_id.round(invoice.amount_residual),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
                invoice.last_installment_reminder_date = today

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if (
            order.installment_plans_id
            and not self.env.context.get("skip_installment_plan")
            and not vals.get("down_payment_amt_ids")
        ):
            plan_vals = order._prepare_installment_plan_values()
            if plan_vals:
                order.with_context(skip_installment_plan=True).write(plan_vals)
        order._recompute_down_payment_totals()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get("installment_ids"):
            for record in self:
                total = sum(record.installment_ids.mapped("amount"))
                if int(total) > record.amount_total:
                    raise UserError(
                        _(
                            "Installment Amount Or Number Of Installment Mismatch Error."
                        )
                    )
        if (
            not self.env.context.get("skip_installment_plan")
            and "installment_plans_id" in vals
            and not vals.get("down_payment_amt_ids")
        ):
            for order in self:
                if order.installment_plans_id:
                    plan_vals = order._prepare_installment_plan_values()
                    if plan_vals:
                        order.with_context(skip_installment_plan=True).write(plan_vals)
        triggers = {"down_payment_amt_ids", "order_line", "amount_total", "tenure"}
        if triggers & set(vals.keys()):
            self._recompute_down_payment_totals()
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        installment_ids = []
        vals = {}

        for order in self:
            dwn_pymnt = 0
            if order.installment_plans_id:
                if order.single_invoice_installment:
                    for payment in order.down_payment_amt_ids:
                        dwn_pymnt += payment.amount
                    vals.update(
                        {
                            "tenure": order.tenure,
                            "installment_amt": order.installment_amt,
                            "down_payment_amt": dwn_pymnt,
                            "payable_amt": order.payable_amt,
                            "single_invoice_installment": True,
                            "multiple_invoice_installment": False,
                        }
                    )
                    for line in order.installment_ids:
                        installment_ids.append(
                            (
                                0,
                                0,
                                {
                                    "index": line.index,
                                    "amount": line.amount,
                                    "payment_date": line.payment_date,
                                    "description": line.description,
                                    "sinst_line_id": line.id,
                                    "is_installment": line.is_installment,
                                },
                            )
                        )
                    vals.update({"installment_ids": installment_ids})
                else:
                    vals.update(
                        {
                            "single_invoice_installment": False,
                            "multiple_invoice_installment": True,
                        }
                    )

        res.update(vals)
        return res

    # ============================
    #     SCHEDULER METHODS
    # ============================
    # days_before_invoice = fields.Integer(
    #     "Days before",
    #     config_parameter="payment_installment_kanak.days_before_invoice",
    #     default=0
    # )
    def check_and_create_invoice(self):
        today_date = fields.Date.today()
        days_before = self.env.company.days_before_invoice
        sale_orders = self.env["sale.order"].search(
            [("multiple_invoice_installment", "=", True)]
        )
        for order in sale_orders:
            # Find installment where payment_date - days_before_invoice == today_date
            # This means invoice is created 'days_before_invoice' days BEFORE the payment date

            installment_to_invoice = None
            for rec in order.installment_ids:
                if rec.state == "draft":  # Only process unpaid installments
                    invoice_date = rec.payment_date - relativedelta(days=days_before)
                    if invoice_date == today_date:
                        installment_to_invoice = rec
                        break
            
            if installment_to_invoice:
                amount = installment_to_invoice.amount
                payment_date = installment_to_invoice.payment_date
                
                # Mark installment as posted (invoice created & posted)
                installment_to_invoice.state = "posted"
                
                # Create wizard using create() instead of Form
                wizard = self.env["sale.advance.payment.inv"].create({
                    "advance_payment_method": "fixed",
                    "fixed_amount": amount,
                    "sale_order_ids": [(6, 0, [order.id])],
                    "target_installment_id": installment_to_invoice.id,
                })
                # Use _create_invoices() which returns invoice recordset directly
                # For fixed method, it returns a single invoice
                invoice = wizard.with_context(
                    open_invoices=False
                )._create_invoices(wizard.sale_order_ids)
                
                # Link invoice to sale installment line
                invoice.sale_installment_line_id = installment_to_invoice.id
                
                invoice.action_post()

                report = self.env["ir.actions.report"]._render_qweb_pdf(
                    "account.account_invoices", [invoice.id]
                )[0]

                filename = (
                    invoice.name + "_" + invoice.payment_reference + ".pdf"
                )
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": filename,
                        "type": "binary",
                        "datas": base64.b64encode(report),
                        "store_fname": filename,
                        "mimetype": "application/x-pdf",
                        "res_model": "account.move",
                        "res_id": invoice.id,
                    }
                )

                action = invoice.action_invoice_sent()
                if action.get("res_model") == "base.document.layout":
                    # Create document layout wizard
                    layout_wizard = self.env["base.document.layout"].create({
                        "font": "Lato",
                        "layout_background": "Blank",
                    })
                    layout_wizard.report_layout_id = (
                        self.env["report.layout"].search([], limit=1).id
                    )
                    layout_wizard.paperformat_id = (
                        self.env["report.paperformat"]
                        .search([("name", "=", "A4")], limit=1)
                        .id
                    )
                    layout_wizard.document_layout_save()
                    # After layout is saved, get the send action again
                    action = invoice.action_invoice_sent()
                
                # Check for Odoo 18 send wizard models
                res_model = action.get("res_model")
                if res_model in ("account.move.send.wizard", "account.move.send.batch.wizard", "account.invoice.send"):
                    # Create invoice send wizard with minimal fields
                    # The wizard will handle email sending automatically
                    email_wizard = self.env[res_model].with_context(
                        active_model="account.move",
                        active_ids=[invoice.id],
                    ).create({})
                    # Call the send method
                    if hasattr(email_wizard, "action_send_and_print"):
                        email_wizard.action_send_and_print()
                    elif hasattr(email_wizard, "_send_email"):
                        email_wizard._send_email()

                    # Create activity for salesperson after invoice is created and email is sent
                    if order.user_id:
                        try:
                            activity_type = self.env.ref(
                                "payment_installment_kanak.mail_activity_data_invoice_sent"
                            )
                        except ValueError:
                            # Fallback to first available activity type if custom one is missing
                            activity_type = self.env["mail.activity.type"].search([], limit=1)
                        
                        if activity_type:
                            due_date = (
                                invoice.invoice_date_due
                                or payment_date
                                or fields.Date.context_today(order)
                            )
                            due_date_str = fields.Date.to_string(due_date) if due_date else ''
                            order.activity_schedule(
                                activity_type_id=activity_type.id,
                                user_id=order.user_id.id,
                                summary=_('Invoice Created and Sent - Installment Payment'),
                                note=_('Invoice %s has been created and sent to customer for installment payment of %s. Payment due date: %s') % (
                                    invoice.name,
                                    amount,
                                    due_date_str
                                ),
                                date_deadline=due_date,
                            )



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    installments = fields.Integer(string="#Installments")

    
