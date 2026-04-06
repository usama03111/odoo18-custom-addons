# -*- coding: utf-8 -*-
from datetime import timedelta, date
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('hr_expense_travel_link')
class TestHrExpenseTravelLink(TransactionCase):

    def setUp(self):
        super().setUp()

        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.travel_request = self.env['employee.travel.request'].create({
            'travel_information': 'Business Trip to HQ',
            'request_departure_date': date.today(),
            'request_return_date': date.today() + timedelta(days=2),
            'expense_sheet': 'single_line',
        })
        self.product = self.env['product.product'].create({
            'name':'test product',
        })

        self.expense = self.env['hr.expense'].create({
            'name': 'Employee expense',
            'product_id': self.product.id,
            'date': date.today(),
            'payment_mode': 'own_account',
            'total_amount': 1000.00,
            'employee_id': self.employee.id,
            'employee_travel_expense_id': self.travel_request.id,
        })

    def test_expense_link_to_travel_request(self):
        """Ensure the expense links properly to a travel request."""
        self.assertEqual(self.expense.employee_travel_expense_id.id, self.travel_request.id)

