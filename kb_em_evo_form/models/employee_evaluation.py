# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError


class EmployeeManagerEvaluation(models.Model):
    _name = "kb.em.evo.form"
    _description = "Employee Manager Evaluation Form"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Reference", default="/", copy=False, readonly=True, tracking=True)

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        tracking=True,
        ondelete="cascade"
    )

    manager_employee_id = fields.Many2one(
        "hr.employee",
        string="Manager (Employee)",
        compute="_compute_manager",
        store=True,
        readonly=True
    )

    manager_user_id = fields.Many2one(
        "res.users",
        string="Manager (User)",
        compute="_compute_manager",
        store=True,
        readonly=True,
        tracking=True
    )

    hr_user_id = fields.Many2one(
        "res.users",
        string="HR Responsible",
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True
    )

    date = fields.Date(string="Date", default=fields.Date.context_today, tracking=True)

    # ✅ NEW: Table lines (criteria + rating 1..5)
    evaluation_line_ids = fields.One2many(
        "kb.em.evo.form.line",
        "evaluation_id",
        string="Manager Evaluation",
        default=lambda self: self._default_evaluation_lines()
    )

    # HR notes
    hr_notes = fields.Text(string="HR Notes", tracking=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent to Manager"),
            ("submitted", "Submitted to HR"),
            ("done", "Done"),
        ],
        default="draft",
        tracking=True,
        required=True
    )

    # ---------------- COMPUTE ----------------
    @api.depends("employee_id", "employee_id.parent_id", "employee_id.parent_id.user_id")
    def _compute_manager(self):
        for rec in self:
            manager_emp = rec.employee_id.parent_id
            rec.manager_employee_id = manager_emp
            rec.manager_user_id = manager_emp.user_id if manager_emp else False

    # ---------------- DEFAULT CRITERIA LINES ----------------
    def _default_evaluation_lines(self):
        return [
            (0, 0, {
                "sequence": 1,
                "category": "القيادة",
                "description": "قدرة الموظف على توجيه وتحفيز الفريق لتحقيق الأهداف",
            }),
            (0, 0, {
                "sequence": 2,
                "category": "التواصل",
                "description": "وضوح وفعالية التواصل مع الآخرين",
            }),
            (0, 0, {
                "sequence": 3,
                "category": "العمل الجماعي",
                "description": "المساهمة الإيجابية في الفريق ودعم الزملاء",
            }),
            (0, 0, {
                "sequence": 4,
                "category": "حل المشكلات",
                "description": "القدرة على تحليل المشكلات واتخاذ قرارات مناسبة",
            }),
            (0, 0, {
                "sequence": 5,
                "category": "الالتزام",
                "description": "الالتزام بالسياسات والقيم وأخلاقيات العمل",
            }),
        ]

    # ---------------- SEQUENCE ----------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("kb.em.evo.form") or "/"
        return super().create(vals_list)

    # ---------- Security helpers ----------
    def _is_hr(self):
        return self.env.user.has_group("kb_em_evo_form.group_hr_employee_evaluation")

    def _is_manager(self):
        return self.env.user.has_group("kb_em_evo_form.group_manager_employee_evaluation")

    def _check_hr(self):
        if not self._is_hr():
            raise AccessError(_("Only HR users can perform this action."))

    def _check_manager(self):
        if not self._is_manager():
            raise AccessError(_("Only Manager users can perform this action."))

    def _check_manager_ownership(self):
        for rec in self:
            if rec.manager_user_id != self.env.user:
                raise AccessError(_("You can only access evaluations assigned to you."))

    # ---------- Workflow actions ----------
    def action_send_to_manager(self):
        self._check_hr()
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("You can only send a Draft evaluation to the manager."))

            if not rec.manager_user_id:
                raise UserError(
                    _("The selected employee does not have a manager with a linked user. "
                      "Set the manager on the employee (Manager field), and ensure the manager employee has a User.")
                )

            rec.state = "sent"

            # Notify manager via chatter + activity
            rec.message_post(
                body=_("Evaluation sent to manager: %s") % (rec.manager_user_id.display_name,),
                partner_ids=[rec.manager_user_id.partner_id.id],
            )
            rec.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=rec.manager_user_id.id,
                summary=_("Employee evaluation feedback requested"),
                note=_("Please fill the evaluation for %s and submit back to HR.") % (rec.employee_id.name,),
            )
        return True

    def action_submit_to_hr(self):
        self._check_manager()
        self._check_manager_ownership()
        for rec in self:
            if rec.state != "sent":
                raise UserError(_("You can only submit an evaluation that is in 'Sent to Manager' state."))

            # Require at least one rating filled
            any_rating = any(line.rating for line in rec.evaluation_line_ids)
            if not any_rating:
                raise UserError(_("Please rate at least one criteria (1-5) before submitting."))

            rec.state = "submitted"
            rec.activity_feedback(["mail.mail_activity_data_todo"])
            rec.message_post(body=_("Manager submitted the evaluation to HR."))
        return True

    def action_done(self):
        self._check_hr()
        for rec in self:
            if rec.state not in ("submitted", "sent"):
                raise UserError(_("You can mark as Done only after submission (or if you decide to close it)."))
            rec.state = "done"
        return True

    def action_reset_to_draft(self):
        self._check_hr()
        for rec in self:
            rec.state = "draft"
        return True
