# POS Loyalty Discount

This module adds a simple loyalty system to the Point of Sale. It automatically applies a discount to order lines based on the selected customer's loyalty score.

## How it Works

We added a `Loyalty Score` integer field to the Customer model (`res.partner`). When you select a customer in the POS interface, the system checks their score and applies a discount to all lines in the current order.

If you add products *after* selecting a customer, the discount is automatically applied to those new lines as well.

## Discount Rules

The discount percentage is hardcoded based on the following tiers:

| Loyalty Score | Discount Applied |
| :--- | :--- |
| **1000+** | 10% |
| **500 - 999** | 5% |
| **< 500** | 0% |

## Technical Details

- **Backend**: Extends `res.partner` to include the `loyalty_score` field and loads it into the POS session.
- **Frontend**: Patches `PosOrder` (to handle customer selection changes) and `PosStore` (to handle new product additions) ensuring the discount is always up-to-date.
