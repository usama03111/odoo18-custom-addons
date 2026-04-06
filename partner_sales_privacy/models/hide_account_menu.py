from odoo import models

class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _visible_menu_ids(self, debug=False):
        visible_ids = super()._visible_menu_ids(debug=debug)
        user = self.env.user

        # ✅ Accounting visibility control
        account_groups = [
            "account.group_account_invoice",
            "account.group_account_user",
            "account.group_account_manager",
        ]

        has_any_account_group = any(user.has_group(group) for group in account_groups)

        # If user has none of the accounting groups, hide accounting menus
        if not has_any_account_group:
            accounting_menu_xml_ids = [
                "account.menu_finance",
            ]

            hidden_account_menu_ids = {
                self.env.ref(xml_id, raise_if_not_found=False).id
                for xml_id in accounting_menu_xml_ids
                if self.env.ref(xml_id, raise_if_not_found=False)
            }

            visible_ids -= hidden_account_menu_ids

        return visible_ids
