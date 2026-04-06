# from odoo import models, fields, api
#
# class SalesInventoryDashboard(models.Model):
#     _name = "custom.kpi.dashboard"
#     _description = "Custom KPI Dashboard for Sales & Inventory"
#     _auto = False  # prevent table creation and record storage
#
#     total_sales = fields.Float(string="Total Sales", compute="_compute_dashboard_values")
#     total_orders = fields.Integer(string="Total Orders", compute="_compute_dashboard_values")
#     total_stock = fields.Float(string="Total Stock", compute="_compute_dashboard_values")
#     salesperson_count = fields.Integer(string="Salesperson Count", compute="_compute_dashboard_values")
#     incoming_stock = fields.Float(string="Incoming Stock", compute="_compute_dashboard_values")
#     outgoing_stock = fields.Float(string="Outgoing Stock", compute="_compute_dashboard_values")
#     total_purchase = fields.Float(string="Total Purchase", compute="_compute_dashboard_values")
#     total_purchase_orders = fields.Integer(string="Total Purchase Orders", compute="_compute_dashboard_values")
#     total_buyers = fields.Integer(string="Buyers", compute="_compute_dashboard_values")
#
#     @api.depends()
#     def _compute_dashboard_values(self):
#         for record in self:
#             confirmed_orders = self.env["sale.order"].search([("state", "=", "sale")])
#             record.total_sales = sum(confirmed_orders.mapped("amount_total"))
#             record.total_orders = len(confirmed_orders)
#
#             products = self.env["product.product"].search([])
#             stock_data = products._compute_quantities_dict(None, None, None)
#             record.total_stock = sum(stock_data[p.id]["qty_available"] for p in products)
#             record.incoming_stock = sum(stock_data[p.id]["incoming_qty"] for p in products)
#             record.outgoing_stock = sum(stock_data[p.id]["outgoing_qty"] for p in products)
#             purchase_orders = self.env["purchase.order"].search([("state", "in", ["purchase", "done"])])
#             record.total_purchase = sum(purchase_orders.mapped("amount_total"))
#             record.total_purchase_orders = len(purchase_orders)
#             record.total_buyers = len(set(purchase_orders.mapped("user_id.id")))
#
#             # Count unique salespersons
#             user_ids = confirmed_orders.mapped("user_id.id")
#             record.salesperson_count = len(set(user_ids))
#
#
#     def search(self, args, offset=0, limit=None, order=None, count=False):
#             """Override search to return one virtual record for dashboard"""
#             dummy_id = self.env.context.get('dashboard_dummy_id', 1)
#             record = self.browse(dummy_id)
#             return [record] if not count else 1
#
#     def read(self, fields=None, load='_classic_read'):
#         """Force read to compute fields even on dummy record"""
#         self._compute_dashboard_values()
#         return super(SalesInventoryDashboard, self).read(fields, load)


from odoo import models, fields, api
from datetime import date

class SalesInventoryDashboard(models.Model):
    _name = "custom.kpi.dashboard"
    _description = "Custom KPI Dashboard for Sales & Inventory"
    _auto = False  # Prevent actual record storage

    # Filters
    start_date = fields.Date(string="Start Date",store=False)
    end_date = fields.Date(string="End Date",store=False)

    # Sales
    total_sales = fields.Float(string="Total Sales", compute="_compute_dashboard_values")
    total_orders = fields.Integer(string="Total Orders", compute="_compute_dashboard_values")
    salesperson_count = fields.Integer(string="Salespersons", compute="_compute_dashboard_values")

    # Purchase
    total_purchase = fields.Float(string="Total Purchase", compute="_compute_dashboard_values")
    total_purchase_orders = fields.Integer(string="Total Purchase Orders", compute="_compute_dashboard_values")
    total_buyers = fields.Integer(string="Buyers", compute="_compute_dashboard_values")

    # Stock
    total_stock = fields.Float(string="Total Stock", compute="_compute_dashboard_values")
    incoming_stock = fields.Float(string="Incoming Stock", compute="_compute_dashboard_values")
    outgoing_stock = fields.Float(string="Outgoing Stock", compute="_compute_dashboard_values")

    @api.depends('start_date', 'end_date')
    def _compute_dashboard_values(self):
        for record in self:
            start_date = record.start_date or date.min
            end_date = record.end_date or date.max

            # Sales KPIs
            sales_domain = [
                ("state", "=", "sale"),
                ("date_order", ">=", start_date),
                ("date_order", "<=", end_date),
            ]
            sale_orders = self.env["sale.order"].search(sales_domain)
            record.total_sales = sum(sale_orders.mapped("amount_total"))
            record.total_orders = len(sale_orders)
            record.salesperson_count = len(set(sale_orders.mapped("user_id.id")))

            # Purchase KPIs
            purchase_domain = [
                ("state", "in", ["purchase", "done"]),
                ("date_order", ">=", start_date),
                ("date_order", "<=", end_date),
            ]
            purchase_orders = self.env["purchase.order"].search(purchase_domain)
            record.total_purchase = sum(purchase_orders.mapped("amount_total"))
            record.total_purchase_orders = len(purchase_orders)
            record.total_buyers = len(set(purchase_orders.mapped("user_id.id")))

            # Stock KPIs (not filtered by date)
            products = self.env["product.product"].search([])
            stock_data = products._compute_quantities_dict(None, None, None)
            record.total_stock = sum(stock_data[p.id]["qty_available"] for p in products)
            record.incoming_stock = sum(stock_data[p.id]["incoming_qty"] for p in products)
            record.outgoing_stock = sum(stock_data[p.id]["outgoing_qty"] for p in products)

    def search(self, args, offset=0, limit=None, order=None, count=False):
        dummy_id = self.env.context.get('dashboard_dummy_id', 1)
        record = self.browse(dummy_id)
        return [record] if not count else 1

    def read(self, fields=None, load='_classic_read'):
        self._compute_dashboard_values()
        return super().read(fields, load)
