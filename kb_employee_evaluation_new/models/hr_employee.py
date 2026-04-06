from odoo import api, fields, models

RATING = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]

class HrEmployee(models.Model):
    _inherit = "hr.employee"

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
    mgr_total = fields.Integer(compute="_compute_eval_totals", store=True)
    self_total = fields.Integer(compute="_compute_eval_totals", store=True)
    final_total = fields.Float(compute="_compute_eval_totals", store=True)
    final_result = fields.Char(compute="_compute_eval_totals", store=True)

    @api.depends(
        "mgr_leadership","mgr_communication","mgr_teamwork","mgr_problem_solving","mgr_commitment",
        "mgr_teamwork_2","mgr_problem_solving_2","mgr_commitment_2",
        "self_leadership","self_communication","self_teamwork","self_problem_solving","self_commitment",
        "self_teamwork_2","self_problem_solving_2","self_commitment_2",
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

            mgr_total = sum(int(v) for v in mgr_vals if v)
            self_total = sum(int(v) for v in self_vals if v)

            rec.mgr_total = mgr_total
            rec.self_total = self_total

            # weights: manager 80% , self 20%
            rec.final_total = (mgr_total * 0.8) + (self_total * 0.2)

            # Result ranges (as your screenshot)
            # 8 items => max 40
            ft = rec.final_total
            if ft >= 35:
                rec.final_result = "ممتاز"
            elif ft >= 28:
                rec.final_result = "جيد جداً"
            elif ft >= 21:
                rec.final_result = "جيد"
            elif ft >= 13:
                rec.final_result = "مقبول"
            else:
                rec.final_result = "ضعيف"
