from odoo import http
from odoo.http import request

class TransportBookingController(http.Controller):

    @http.route("/transport/data", type="json", auth="user")
    def load_data(self):
        # Fetching all required fields for the UI
        routes = request.env["transport.route"].search_read([], ["name", "start_location", "end_location"])
        vehicles = request.env["transport.vehicle"].search_read([], ["name", "capacity"])
        return {
            "routes": routes,
            "vehicles": vehicles,
        }

    @http.route("/transport/booking/create", type="json", auth="user")
    def create_booking(self, data):
        # Delegating to the model method
        return request.env["transport.booking"].create_booking(data)
