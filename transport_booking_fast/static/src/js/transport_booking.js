/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

// CLASS DEFINITION
export class TransportBooking extends Component {
    setup() {
        this.state = useState({
            routes: [],
            vehicles: [],
            selectedRoute: null,
            selectedVehicle: null,
            customerName: "",
            seats: 1,
            amount: 0.0,
        });
        console.log("state....",this.state);

        onWillStart(async () => {
            try {
                // Direct call to controller route
                const data = await rpc("/transport/data");
                this.state.routes = data.routes;
                this.state.vehicles = data.vehicles;
                console.log("data....",data);
            } catch (error) {
                console.error("Failed to load master data:", error);

            }
        });
    }
     //  CUSTOM METHOD CALLED BY BUTTON WHEN CLICK
    async confirmBooking() {
        const bookingData = {
            route_id: parseInt(this.state.selectedRoute),
            vehicle_id: parseInt(this.state.selectedVehicle),
            customer_name: this.state.customerName,
            seats: parseInt(this.state.seats),
            amount: parseFloat(this.state.amount),
        };
        console.log("booking data....",bookingData);

        if (!bookingData.route_id || !bookingData.vehicle_id || !bookingData.customer_name) {
            alert("Please fill in all fields.");
            return;
        }

        try {
            // Direct call to controller route
            const result = await rpc("/transport/booking/create", { data: bookingData });
            if (result.success) {
                this.state.selectedRoute = null;
                this.state.selectedVehicle = null;
                this.state.customerName = "";
                this.state.seats = 1;
                this.state.amount = 0.0;
                alert("Booking Confirmed!");
                console.log("result....",result);
            }
        } catch (error) {
            console.error("Booking failed:", error);
            alert("An error occurred during booking.");
        }
    }
}
//  TEMPLATE MAPPING
TransportBooking.template = "transport_booking_fast.TransportBooking";
//console.log("templete....",template);
// ACTION REGISTRATION
registry.category("actions").add("transport_booking_fast.TransportBooking", TransportBooking);
console.log("transport booking....",TransportBooking);
