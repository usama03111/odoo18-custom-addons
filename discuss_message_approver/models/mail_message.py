from odoo import models, fields

# Try to import Store, if it fails (unlikely in Odoo 18), we might need another approach or it's available via odoo.addons.
try:
    from odoo.addons.mail.tools.discuss import Store
except ImportError:
    # If this import fails, it means we are in an older environment or path is different.
    # But based on the user provided file, this is the correct path.
    Store = None

class Message(models.Model):
    _inherit = 'mail.message'

    approval_task_id = fields.Many2one('project.task', string='Approval Task')
    approval_task_state = fields.Selection(related='approval_task_id.state', string='Approval Task State')

    def _to_store(self, store, **kwargs):
        """Override to include approval_task_id in the message data sent to the web client."""
        super()._to_store(store, **kwargs)
        for message in self:
            if message.approval_task_id:
                store.add(message, {
                    "approval_task_id": message.approval_task_id.id,
                    "approval_task_state": message.approval_task_state,
                })
