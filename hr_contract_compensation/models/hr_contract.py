from odoo import models, fields,api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    gen_allowance = fields.Monetary(
        string="Gen.Allow",
        currency_field='currency_id',
        tracking=True,
    )

    # --------------------
    # Allowances
    # --------------------
    phone_allow = fields.Monetary(string="Phone Allowance", currency_field='currency_id',tracking=True,)
    food_allow = fields.Monetary(string="Food Allowance", currency_field='currency_id',tracking=True,)
    hra = fields.Monetary(string="HRA", currency_field='currency_id' , tracking=True,)
    transportation = fields.Monetary(string="Transportation", currency_field='currency_id' , tracking=True,)
    other_income = fields.Monetary(string="Other Income", currency_field='currency_id' , tracking=True,)

    total_allowance_month = fields.Monetary(
        string="Total Allowances (Monthly)",
        currency_field='currency_id',
        compute="_compute_total_allowance",
        store=True
    )

    # --------------------
    # Deductions
    # --------------------
    other_deduction = fields.Monetary(string="Other Deduction", currency_field='currency_id' , tracking=True,)
    hold_paid = fields.Monetary(string="Hold / Paid", currency_field='currency_id' , tracking=True,)
    training_amount = fields.Monetary(string="Training Amount", currency_field='currency_id' , tracking=True,)

    total_deduction = fields.Monetary(
        string="Total Deductions",
        currency_field='currency_id',
        compute="_compute_total_deduction",
        store=True
    )

    # --------------------
    # Cost Calculation
    # --------------------
    monthly_cost = fields.Monetary(
        string="Monthly Cost",
        currency_field='currency_id',
        compute="_compute_cost",
        store=True
    )

    yearly_cost = fields.Monetary(
        string="Yearly Cost",
        currency_field='currency_id',
        compute="_compute_cost",
        store=True
    )

    # text fields
    airfare_policy = fields.Text(
        string="Airfare Policy",
        translate=True,
        tracking=True
    )

    annual_vacation_policy = fields.Text(
        string="Annual Vacation Policy",
        translate=True
    )

    medical_care_policy = fields.Text(
        string="Medical Care Policy",
        translate=True
    )

    offer_subject_to = fields.Text(
        string="Offer Subject To",
        translate=True
    )

    governing_law = fields.Text(
        string="Governing Law",
        translate=True
    )

    offer_validity = fields.Text(
        string="Offer Validity",
        translate=True
    )

    probation_period = fields.Text(
        string="Probation Period",
        translate=True,
    )

    employee_grade = fields.Char(string="Employee Grade")
    owner_name = fields.Char(string="Owner Name")

    # --------------------
    # Compute Methods
    # --------------------

    @api.depends('phone_allow', 'food_allow', 'hra', 'transportation', 'other_income', 'gen_allowance')
    def _compute_total_allowance(self):
        """
        Compute the total monthly allowance by summing up individual components.
        """
        for rec in self:
            rec.total_allowance_month = (
                rec.phone_allow +
                rec.food_allow +
                rec.hra +
                rec.transportation +
                rec.other_income +
                rec.gen_allowance
            )

    @api.depends('other_deduction', 'hold_paid', 'training_amount')
    def _compute_total_deduction(self):
        """
        Compute the total deductions by summing up individual deduction components.
        """
        for rec in self:
            rec.total_deduction = (
                rec.other_deduction +
                rec.hold_paid +
                rec.training_amount
            )

    @api.depends('wage', 'total_allowance_month', 'total_deduction')
    def _compute_cost(self):
        """
        Compute the monthly and yearly cost of the contract based on wage, allowances, and deductions.
        """
        for rec in self:
            rec.monthly_cost = (
                rec.wage +
                rec.total_allowance_month -
                rec.total_deduction
            )
            rec.yearly_cost = rec.monthly_cost * 12


