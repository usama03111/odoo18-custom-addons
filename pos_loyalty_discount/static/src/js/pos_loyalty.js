/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosStore } from "@point_of_sale/app/store/pos_store";


// We patch 'PosOrder' class to add logic that applies discounts when a customer is set or changed.
patch(PosOrder.prototype, {
    set_partner(partner) {
        super.set_partner(...arguments);
        const discount = this._get_loyalty_discount(partner);

        for (const line of this.get_orderlines()) {
            line.set_discount(discount);
        }
    },

    // This function calculates discount based on the customer’s loyalty score.
    _get_loyalty_discount(partner) {
        if (!partner) {
            return 0;
        }
        const score = partner.loyalty_score || 0;
        if (score >= 1000) {
            return 10;
        } else if (score >= 500) {
            return 5;
        }
        return 0;
    },
});

// We patch 'PosStore' to handle the case where a product is added AFTER a customer is already selected.
patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const line = await super.addLineToOrder(...arguments);
        if (line && order) {
            const partner = order.get_partner();
            if (partner) {
                const discount = order._get_loyalty_discount(partner);
                // We immediately set the discount on this newly added line.
                line.set_discount(discount);
            }
        }
        // Finally, we return the line object as the original method expects.
        return line;
    },
});
