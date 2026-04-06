from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    hide_sales_tab = fields.Boolean(
        string="Hide Sales Tab",
        compute="_compute_hide_tabs",
        store=False
    )
    hide_account_tab = fields.Boolean(
        string="Hide Accounting Tab",
        compute="_compute_hide_tabs",
        store=False
    )

    @api.depends_context('uid')
    def _compute_hide_tabs(self):
        user = self.env.user
        # Sales groups
        sales_groups = [
            'sales_team.group_sale_salesman',
            'sales_team.group_sale_salesman_all_leads',
            'sales_team.group_sale_manager',
        ]

        # Accounting groups
        account_groups = [
            'account.group_account_invoice',
            'account.group_account_user',
            'account.group_account_manager',
        ]

        for rec in self:
            has_sales_access = any(user.has_group(g) for g in sales_groups)
            has_account_access = any(user.has_group(g) for g in account_groups)

            # Hide tabs only if user has none of the relevant groups
            rec.hide_sales_tab = not has_sales_access
            rec.hide_account_tab = not has_account_access


