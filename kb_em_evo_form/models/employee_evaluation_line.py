# -*- coding: utf-8 -*-
from odoo import models, fields


class EmployeeEvaluationLine(models.Model):
    _name = "kb.em.evo.form.line"
    _description = "Employee Evaluation Criteria Line"
    _order = "sequence, id"

    evaluation_id = fields.Many2one(
        "kb.em.evo.form",
        ondelete="cascade",
        required=True
    )

    sequence = fields.Integer(string="#", default=10)

    category = fields.Char(
        string="المجال",
        required=True
    )

    description = fields.Text(
        string="الوصف"
    )

    rating = fields.Selection(
        [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
        ],
        string="التقييم",
    )
