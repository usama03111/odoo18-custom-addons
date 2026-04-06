/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";

const passwordCopyAction = async (env, action) => {
    const password = action.params && action.params.password;
    if (password) {
        try {
            await browser.navigator.clipboard.writeText(password);
            env.services.notification.add(_t("Password copied to clipboard"), {
                type: "success",
            });
        } catch (err) {
            env.services.notification.add(_t("Failed to copy password"), {
                type: "danger",
            });
            console.error(err);
        }
    } else {
        env.services.notification.add(_t("No password to copy"), {
            type: "warning",
        });
    }
    return { type: "ir.actions.act_window_close" };
};

registry.category("actions").add("password_manager.copy_to_clipboard", passwordCopyAction);
