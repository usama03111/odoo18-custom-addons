from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
from dateutil.relativedelta import relativedelta

class PaymentTerm(models.Model):
    _inherit = "account.payment.term"

    name = fields.Char(
        string="Installment Plans", translate=True, required=True
    )
    installment_due_days = fields.Integer(
        string="Installment Due In Days",
        default=30,
        help="Number of days after the invoice date to set the due date "
        "when invoices are generated per installment.",
    )
    line_ids = fields.One2many(
        "account.payment.term.line",
        "payment_id",
        string="Terms",
        copy=True,
        default=False,
    )

    is_plan = fields.Boolean()

    sale_order_id = fields.Many2one("sale.order", string="Sale Order")

    @api.constrains('line_ids', 'early_discount')
    def _check_lines(self):
        """Override to handle both balance lines (Odoo 16 style) and percent lines (Odoo 18 style)"""
        round_precision = self.env['decimal.precision'].precision_get('Payment Terms')
        for terms in self:
            # Check if using balance lines (Odoo 16 style)
            balance_lines = terms.line_ids.filtered(lambda r: r.value == 'balance')
            if balance_lines:
                # Odoo 16 validation: must have exactly one balance line
                if len(balance_lines) != 1:
                    raise ValidationError(_('The Payment Term must have one Balance line.'))
                # Check for fixed amount with early payment percentage
                if terms.line_ids.filtered(lambda r: r.value == 'fixed' and r.discount_percentage):
                    raise ValidationError(_("You can't mix fixed amount with early payment percentage"))
            else:
                # Odoo 18 validation: percent lines must sum to 100%
                total_percent = sum(line.value_amount for line in terms.line_ids if line.value == 'percent')
                if float_round(total_percent, precision_digits=round_precision) != 100:
                    raise ValidationError(_('The Payment Term must have at least one percent line and the sum of the percent must be 100%.'))

            # Early discount validations (common for both)
            if len(terms.line_ids) > 1 and terms.early_discount:
                raise ValidationError(
                    _("The Early Payment Discount functionality can only be used with payment terms using a single 100% line. "))
            if terms.early_discount and terms.discount_percentage <= 0.0:
                raise ValidationError(_("The Early Payment Discount must be strictly positive."))
            if terms.early_discount and terms.discount_days <= 0:
                raise ValidationError(_("The Early Payment Discount days must be strictly positive."))

    def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, cash_rounding=None):
        """Override to handle balance lines (Odoo 16 style) when present"""
        self.ensure_one()

        # Check if using balance lines (Odoo 16 style)
        balance_lines = self.line_ids.filtered(lambda r: r.value == 'balance')
        if balance_lines:
            # Use Odoo 16 style computation for balance lines
            return self._compute_terms_odoo16_style(
                date_ref, currency, company, tax_amount, tax_amount_currency,
                sign, untaxed_amount, untaxed_amount_currency, cash_rounding
            )
        else:
            # Use Odoo 18 style computation (default)
            return super(PaymentTerm, self)._compute_terms(
                date_ref, currency, company, tax_amount, tax_amount_currency,
                sign, untaxed_amount, untaxed_amount_currency, cash_rounding
            )

    def _compute_terms_odoo16_style(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, cash_rounding=None):
        """Compute terms using Odoo 16 style (with balance lines)"""
        company_currency = company.currency_id
        tax_amount_left = tax_amount
        tax_amount_currency_left = tax_amount_currency
        untaxed_amount_left = untaxed_amount
        untaxed_amount_currency_left = untaxed_amount_currency
        total_amount = tax_amount + untaxed_amount
        total_amount_currency = tax_amount_currency + untaxed_amount_currency
        foreign_rounding_amount = 0
        company_rounding_amount = 0
        result = []

        # Sort lines so balance comes last (Odoo 16 behavior)
        for line in self.line_ids.sorted(lambda line: line.value == 'balance'):
            term_vals = {
                'date': line._get_due_date(date_ref),
                'has_discount': line.discount_percentage,
                'discount_date': None,
                'discount_amount_currency': 0.0,
                'discount_balance': 0.0,
                'discount_percentage': line.discount_percentage,
            }

            if line.value == 'fixed':
                term_vals['company_amount'] = sign * company_currency.round(line.value_amount)
                term_vals['foreign_amount'] = sign * currency.round(line.value_amount)
                company_proportion = tax_amount/untaxed_amount if untaxed_amount else 1
                foreign_proportion = tax_amount_currency/untaxed_amount_currency if untaxed_amount_currency else 1
                line_tax_amount = company_currency.round(line.value_amount * company_proportion) * sign
                line_tax_amount_currency = currency.round(line.value_amount * foreign_proportion) * sign
                line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
                line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
            elif line.value == 'percent':
                term_vals['company_amount'] = company_currency.round(total_amount * (line.value_amount / 100.0))
                term_vals['foreign_amount'] = currency.round(total_amount_currency * (line.value_amount / 100.0))
                line_tax_amount = company_currency.round(tax_amount * (line.value_amount / 100.0))
                line_tax_amount_currency = currency.round(tax_amount_currency * (line.value_amount / 100.0))
                line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
                line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
            else:
                line_tax_amount = line_tax_amount_currency = line_untaxed_amount = line_untaxed_amount_currency = 0.0

            # The following values do not account for any potential cash rounding
            tax_amount_left -= line_tax_amount
            tax_amount_currency_left -= line_tax_amount_currency
            untaxed_amount_left -= line_untaxed_amount
            untaxed_amount_currency_left -= line_untaxed_amount_currency

            if cash_rounding and line.value in ['fixed', 'percent']:
                cash_rounding_difference_currency = cash_rounding.compute_difference(currency, term_vals['foreign_amount'])
                if not currency.is_zero(cash_rounding_difference_currency):
                    rate = abs(term_vals['foreign_amount'] / term_vals['company_amount']) if term_vals['company_amount'] else 1.0

                    foreign_rounding_amount += cash_rounding_difference_currency
                    term_vals['foreign_amount'] += cash_rounding_difference_currency

                    company_amount = company_currency.round(term_vals['foreign_amount'] / rate)
                    cash_rounding_difference = company_amount - term_vals['company_amount']
                    if not currency.is_zero(cash_rounding_difference):
                        company_rounding_amount += cash_rounding_difference
                        term_vals['company_amount'] = company_amount

            if line.value == 'balance':
                # The `*_amount_left` variables do not account for cash rounding.
                # Here we remove the total amount added by the cash rounding from the amount left.
                term_vals['foreign_amount'] = tax_amount_currency_left + untaxed_amount_currency_left - foreign_rounding_amount
                term_vals['company_amount'] = tax_amount_left + untaxed_amount_left - company_rounding_amount

                line_tax_amount = tax_amount_left
                line_tax_amount_currency = tax_amount_currency_left
                line_untaxed_amount = untaxed_amount_left
                line_untaxed_amount_currency = untaxed_amount_currency_left

            if line.discount_percentage:
                # In Odoo 18, early_pay_discount_computation is on payment term, not company
                # Check if company has it (Odoo 16 style) or use payment term's field (Odoo 18 style)
                discount_computation = getattr(company, 'early_pay_discount_computation', None)
                if not discount_computation:
                    discount_computation = self.early_pay_discount_computation or 'included'

                if discount_computation in ('excluded', 'mixed'):
                    term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] - line_untaxed_amount * line.discount_percentage / 100.0)
                    term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] - line_untaxed_amount_currency * line.discount_percentage / 100.0)
                else:
                    term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] * (1 - (line.discount_percentage / 100.0)))
                    term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] * (1 - (line.discount_percentage / 100.0)))
                term_vals['discount_date'] = date_ref + relativedelta(days=line.discount_days)

            if cash_rounding and line.discount_percentage:
                cash_rounding_difference_currency = cash_rounding.compute_difference(currency, term_vals['discount_amount_currency'])
                if not currency.is_zero(cash_rounding_difference_currency):
                    rate = abs(term_vals['discount_amount_currency'] / term_vals['discount_balance']) if term_vals['discount_balance'] else 1.0
                    term_vals['discount_amount_currency'] += cash_rounding_difference_currency
                    term_vals['discount_balance'] = company_currency.round(term_vals['discount_amount_currency'] / rate)

            result.append(term_vals)

        # Convert to Odoo 18 format (dictionary with 'line_ids')
        # Odoo 18 expects: {'total_amount': ..., 'discount_percentage': ..., 'line_ids': [...]}
        total_amount = tax_amount + untaxed_amount
        pay_term = {
            'total_amount': total_amount,
            'discount_percentage': 0.0,
            'discount_date': False,
            'discount_balance': 0,
            'line_ids': result,
        }
        return pay_term

class PaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    description = fields.Char()
    period = fields.Selection(
        [("month", "Monthly"), ("quater", "Quarterly"), ("days", "Days")],
        string="Period",
        default="month",
    )
    value = fields.Selection(selection_add=[
        ('balance', 'Balance'),
    ],ondelete={'balance': 'set default'})
    start_date = fields.Date("Start Date")
    months = fields.Integer(string='Months', required=True, default=0)
    days = fields.Integer(string='Days', required=True, default=0)
    end_month = fields.Boolean(string='End of month',
                               help="Switch to end of the month after having added months or days")
    days_after = fields.Integer(string='Days after End of month', help="Days to add after the end of the month")
    discount_percentage = fields.Float(string='Discount %', help='Early Payment Discount granted for this line')
    discount_days = fields.Integer(string='Discount Days',
                                   help='Number of days before the early payment proposition expires')

    def _get_due_date(self, date_ref):
        """Override to support both Odoo 16 style (months/days/end_month/days_after)
        and Odoo 18 style (delay_type/nb_days)"""
        self.ensure_one()
        due_date = fields.Date.from_string(date_ref) or fields.Date.today()

        # If using Odoo 16 style fields (months/days/end_month/days_after)
        if self.months or self.days or self.end_month or self.days_after:
            due_date += relativedelta(months=self.months)
            due_date += relativedelta(days=self.days)
            if self.end_month:
                due_date += relativedelta(day=31)
                due_date += relativedelta(days=self.days_after)
            return due_date

        # Otherwise use Odoo 18 style (delay_type/nb_days)
        return super(PaymentTermLine, self)._get_due_date(date_ref)

    # @api.constrains('start_date')
    # def _constrains_start_date(self):
    #     for rec in self:
    #         if rec.start_date > 28:
    #             raise UserError("The start date cannot be greater than 28.")

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _default_target_installment(self):
        active_id = self.env.context.get("active_id")
        active_model = self.env.context.get("active_model")
        if active_model == "sale.order" and active_id:
            sale = self.env["sale.order"].browse(active_id)
            target_line = sale._get_next_installment_line()
            return target_line.id if target_line else False
        return False

    def _get_amount(self):
        active_id = self._context.get("active_id")
        srch_sale = self.env["sale.order"].browse(active_id)
        amount = 0
        if srch_sale.multiple_invoice_installment:
            target_line = self.target_installment_id or srch_sale._get_next_installment_line()
            if target_line:
                amount = target_line.amount
        return amount

    def _get_payment_method(self):
        active_id = self._context.get("active_id")
        srch_sale = self.env["sale.order"].browse(active_id)
        result = ""
        if srch_sale.installment_plans_id:
            if srch_sale.multiple_invoice_installment:
                result = "fixed"
            else:
                result = "delivered"
        else:
            result = "delivered"
        return result

    def _get_enable_installment(self):
        active_id = self._context.get("active_id")
        srch_sale = self.env["sale.order"].browse(active_id)
        if srch_sale.enable_installment:
            return True
        else:
            return False


    enable_installment = fields.Boolean(default=_get_enable_installment)

    amount = fields.Float(
        string="Down Payment Amount",
        help="The percentage of amount to be invoiced in advance, taxes excluded.",
        default=_get_amount,
    )

    advance_payment_method = fields.Selection(
        selection=[
            ("delivered", "Regular invoice"),
            ("percentage", "Down payment (percentage)"),
            ("fixed", "Down payment (fixed amount)"),
        ],
        string="Create Invoice",
        default=_get_payment_method,
        required=True,
        help="A standard invoice is issued with all the order lines ready for invoicing,"
        "according to their invoicing policy (based on ordered or delivered quantity).",
    )

    # is_installment_plans = fields.Boolean(default=is_installment)

    fixed_amount = fields.Monetary(
        string="Down Payment Amount (Fixed)",
        help="The fixed amount to be invoiced in advance, taxes excluded.",
        default=_get_amount)
    target_installment_id = fields.Many2one(
        "sale.installment.line",
        string="Target Installment",
        default=_default_target_installment,
        help="Installment line that will be invoiced in multiple-invoice mode.",
    )

    def create_invoices(self):
        """Override to link invoice to sale installment line in multiple invoice mode."""
        # Call super to create invoices
        result = super(SaleAdvancePaymentInv, self).create_invoices()
        
        # After invoice creation, link the invoice to the sale installment line
        for order in self.sale_order_ids:
            if order.multiple_invoice_installment and self.target_installment_id:
                target_line = self.target_installment_id
                if target_line and target_line.sale_id == order and target_line.state == "draft":
                    # Mark installment as posted and link to invoice
                    target_line.state = "posted"
                    # Find the invoice that was just created for this order
                    # The most recent invoice linked to this order
                    invoice = order.invoice_ids.sorted('create_date', reverse=True)[:1]
                    if invoice:
                        invoice.sale_installment_line_id = target_line.id
        
        return result

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    is_installment_payment = fields.Boolean()
    is_part_payment = fields.Boolean()
    part_amt = fields.Float()
    installment_lines = fields.Char()

    def _get_total_amount_using_same_currency(self, batch_result, early_payment_discount=True):
        self.ensure_one()
        amount = 0.0
        mode = False
        for aml in batch_result['lines']:
            if early_payment_discount and aml._is_eligible_for_early_payment_discount(aml.currency_id, self.payment_date):
                amount += aml.discount_amount_currency
                mode = 'early_payment'
            else:
                amount += aml.amount_residual_currency
        if self.is_installment_payment or self.is_part_payment:
            amount = self.amount
        return abs(amount), mode

    def action_create_payments(self):
        if self.is_part_payment:
            part_line_inv = {
                "index": 1,
                "amount": self.part_amt,
                "payment_date": fields.Date.today(),
                "description": "Part Payment",
                "invoice_id": self.env.context["active_id"],
                "state": 'paid',
                "journal_id": self.journal_id.id,
                "register_payment_date": self.payment_date,
            }
            installment_ids = eval(self.installment_lines)
            srch_invoice = self.env['account.move'].browse(self._context['active_id'])
            srch_sale = srch_invoice.installment_ids[0].sinst_line_id.sale_id

            part_line_sale = {
                "index": 1,
                "amount": self.part_amt,
                "payment_date": fields.Date.today(),
                "description": "Part Payment",
                "sale_id": srch_sale.id,
                "state": 'paid'
            }

            installment_part_lines = srch_invoice.installment_ids.filtered(lambda x: x.id in installment_ids)


            inv_line_id = self.env['invoice.installment.line'].create(part_line_inv)
            sale_line_id = self.env['sale.installment.line'].create(part_line_sale)

            install_amt = sum(installment_part_lines.mapped('amount'))
            if install_amt == self.part_amt:
                for line in installment_part_lines:
                    line.state = 'paid'
                    line.sinst_line_id.state = 'paid'
            else:
                for line in installment_part_lines:
                    temp = line.amount
                    if line.amount < self.part_amt:
                        line.amount = 0
                        line.state = "paid"
                        line.sinst_line_id.amount = 0
                        line.sinst_line_id.state = "paid"
                    else:
                        line.amount -= self.part_amt
                        line.sinst_line_id.amount -= self.part_amt
                        break
                    self.part_amt -= temp
        
        # Handle multiple invoice installment scenario
        # Get invoices from line_ids (account.move.line) which is the payment register's source
        invoices = self.env["account.move"]
        if hasattr(self, 'line_ids') and self.line_ids:
            # line_ids are account.move.line records, get their parent moves (invoices)
            invoices = self.line_ids.mapped('move_id')
        
        result = super(AccountPaymentRegister, self).action_create_payments()

        # Update sale installment line state to paid for multiple invoice installments
        for invoice in invoices.filtered(
            lambda inv: inv.multiple_invoice_installment and inv.sale_installment_line_id
        ):
            invoice.sale_installment_line_id.state = "paid"

        return result

