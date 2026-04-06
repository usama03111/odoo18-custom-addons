from odoo import models

class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _visible_menu_ids(self, debug=False):
        visible_ids = super()._visible_menu_ids(debug=debug)
        user = self.env.user

        if user.has_group("hr_employee_profile_self_service.group_hr_employee_self_service"):
            menu_xml_ids = [
                "hr.menu_human_resources_configuration",
                "hr.hr_menu_hr_reports",
                "hr.menu_hr_department_kanban",
            ]

            # Collect menu IDs into a set
            hidden_menu_ids = {
                self.env.ref(xml_id, raise_if_not_found=False).id
                for xml_id in menu_xml_ids
                if self.env.ref(xml_id, raise_if_not_found=False)
            }

            # Remove them from the visible menus
            visible_ids -= hidden_menu_ids

        return visible_ids