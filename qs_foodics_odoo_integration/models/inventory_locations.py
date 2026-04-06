from odoo import fields, models, _
import logging

_logger = logging.getLogger(__name__)

class InventLocations(models.Model):
    _inherit = 'stock.location'

    foodics_branch_id = fields.Char('Foodics Branch ID', index=True)

    def set_locations_to_odoo(self, res):
        _logger.info('called the locations method')
        for branch in res.get('data'):

            vals = {
                'foodics_branch_id': branch.get('id'),
                'name': branch.get('name'),
                'usage': "internal"
                # check with implementors if they need other options to be checked such as replinshment
                }
            branch_id = self.search([('foodics_branch_id', '=', branch.get('id'))], limit=1)
            if branch_id:
                branch_id.update(vals)
            else:
                branch_id.create(vals)
