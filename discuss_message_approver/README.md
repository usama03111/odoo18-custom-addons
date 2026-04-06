# Discuss Message Approver

**Category:** Discuss
**Version:** 18.0.1.0.0

## Summary
Add Approver option to Discuss messages

## How It Works
This module adds an inline approval workflow directly to Odoo Discuss messages. 
- **Create Task Action**: A new "Create Task" action button is added to discuss messages. When clicked, it opens a wizard to create a Project Task related to the message. The message's text and any attachments are automatically pulled into the task's description, and attachments are made public.
- **Workflow Tracking**: Once the task is created, the message updates to display a green "Task Created" icon. You can click on this icon to immediately open the linked project task.
- **Approval Status**: The message will be updated with an "Approved" checkmark icon once the associated project task reaches the `1_done` state, making it easy to track whether a request made in chat has been successfully approved and completed.
