/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { messageActionsRegistry } from "@mail/core/common/message_actions";

messageActionsRegistry.add("create_task", {
    condition: (component) => !component.props.message.approval_task_id,
    icon: "fa fa-check",
    title: _t("Create Task"),
    onClick: (component) => {
        const message = component.props.message;
        component.env.services.action.doAction("discuss_message_approver.action_discuss_message_approver_wizard", {
            additionalContext: {
                //default_name: message.body ? message.body.replace(/<[^>]*>?/gm, '').trim() : _t("New Task"),
                default_message_id: message.id,
            },
        });
    },
    sequence: 120,
});

messageActionsRegistry.add("task_created", {
    condition: (component) => component.props.message.approval_task_id,
    icon: "fa fa-check-circle text-success",
    title: _t("Task Created"),
    onClick: (component) => {
        const message = component.props.message;
        component.env.services.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            res_id: message.approval_task_id,
            views: [[false, 'form']],
            target: 'current',
        });
    },
    sequence: 120,
});

messageActionsRegistry.add("approved_task", {
    condition: (component) => component.props.message.approval_task_state === '1_done',
    icon: "fa fa-check text-success",
    title: _t("Approved"),
    onClick: (component) => {
    },
    sequence: 20,
});
