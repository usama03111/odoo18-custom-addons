from odoo import api, fields, models

RATING = [(str(i), str(i)) for i in range(1, 6)]  # 1..5

RESULTS = [
    ("excellent", "ممتاز"),
    ("very_good", "جيد جداً"),
    ("good", "جيد"),
    ("acceptable", "مقبول"),
    ("weak", "ضعيف"),
]


class HrEmployeeManagerEvaluation(models.Model):
    _name = "hr.employee.manager.evaluation"
    _description = "Employee Manager Evaluation"
    _order = "year desc, id desc"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade", index=True)
    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year, index=True)
    date = fields.Date(default=fields.Date.context_today, index=True)

    # -------- Manager Evaluation (8 items) --------
    mgr_leadership = fields.Selection(RATING, string="Manager - Leadership")
    mgr_communication = fields.Selection(RATING, string="Manager - Communication")
    mgr_teamwork = fields.Selection(RATING, string="Manager - Teamwork")
    mgr_problem_solving = fields.Selection(RATING, string="Manager - Problem Solving")
    mgr_commitment = fields.Selection(RATING, string="Manager - Commitment")
    mgr_teamwork_2 = fields.Selection(RATING, string="Manager - Teamwork 2")
    mgr_problem_solving_2 = fields.Selection(RATING, string="Manager - Problem Solving 2")
    mgr_commitment_2 = fields.Selection(RATING, string="Manager - Commitment 2")

    # -------- Self Evaluation (8 items) --------
    self_leadership = fields.Selection(RATING, string="Self - Leadership")
    self_communication = fields.Selection(RATING, string="Self - Communication")
    self_teamwork = fields.Selection(RATING, string="Self - Teamwork")
    self_problem_solving = fields.Selection(RATING, string="Self - Problem Solving")
    self_commitment = fields.Selection(RATING, string="Self - Commitment")
    self_teamwork_2 = fields.Selection(RATING, string="Self - Teamwork 2")
    self_problem_solving_2 = fields.Selection(RATING, string="Self - Problem Solving 2")
    self_commitment_2 = fields.Selection(RATING, string="Self - Commitment 2")

    # Totals
    mgr_total = fields.Integer(compute="_compute_eval_totals", store=True, readonly=True)
    self_total = fields.Integer(compute="_compute_eval_totals", store=True, readonly=True)

    mgr_weighted = fields.Float(compute="_compute_eval_totals", store=True, readonly=True)
    self_weighted = fields.Float(compute="_compute_eval_totals", store=True, readonly=True)

    final_total = fields.Float(compute="_compute_eval_totals", store=True, readonly=True)
    final_result = fields.Selection(RESULTS, compute="_compute_eval_totals", store=True, readonly=True)

    _sql_constraints = [
        ("employee_year_unique", "unique(employee_id, year)",
         "An evaluation already exists for this employee in this year."),
    ]

    def _sum_ratings(self, values):
        return sum(int(v) for v in values if v)

    @api.depends(
        "mgr_leadership", "mgr_communication", "mgr_teamwork", "mgr_problem_solving", "mgr_commitment",
        "mgr_teamwork_2", "mgr_problem_solving_2", "mgr_commitment_2",
        "self_leadership", "self_communication", "self_teamwork", "self_problem_solving", "self_commitment",
        "self_teamwork_2", "self_problem_solving_2", "self_commitment_2",
    )
    def _compute_eval_totals(self):
        for rec in self:
            mgr_vals = [
                rec.mgr_leadership, rec.mgr_communication, rec.mgr_teamwork, rec.mgr_problem_solving,
                rec.mgr_commitment, rec.mgr_teamwork_2, rec.mgr_problem_solving_2, rec.mgr_commitment_2
            ]
            self_vals = [
                rec.self_leadership, rec.self_communication, rec.self_teamwork, rec.self_problem_solving,
                rec.self_commitment, rec.self_teamwork_2, rec.self_problem_solving_2, rec.self_commitment_2
            ]

            mgr_total = rec._sum_ratings(mgr_vals)  # max 40
            self_total = rec._sum_ratings(self_vals)  # max 40

            rec.mgr_total = mgr_total
            rec.self_total = self_total

            rec.mgr_weighted = mgr_total * 0.8
            rec.self_weighted = self_total * 0.2

            ft = rec.mgr_weighted + rec.self_weighted
            rec.final_total = ft

            if ft >= 35:
                rec.final_result = "excellent"
            elif ft >= 28:
                rec.final_result = "very_good"
            elif ft >= 21:
                rec.final_result = "good"
            elif ft >= 13:
                rec.final_result = "acceptable"
            else:
                rec.final_result = "weak"
