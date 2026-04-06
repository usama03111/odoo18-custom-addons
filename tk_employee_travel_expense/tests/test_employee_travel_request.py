# -*- coding: utf-8 -*-
from datetime import timedelta, date
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('employee_travel_request')
class TestEmployeeTravelRequest(TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })

        self.mode = self.env['departure.mode'].create({
            'departure_mode': 'Flight',
        })

        self.travel_request = self.env['employee.travel.request'].create({
            'travel_information': 'Business Trip to HQ',
            'request_departure_date': date.today(),
            'request_return_date': date.today() + timedelta(days=2),
            'travel_mode_id': self.mode.id,
            'expense_sheet': 'single_line',
        })

    def test_create_travel_expense_request(self):
        """Test that travel request is created correctly."""
        self.assertEqual(self.travel_request.state, 'draft')
        self.assertEqual(self.travel_request.trip_days, 3)
        self.assertEqual(self.travel_request.expense_sheet, 'single_line')

    def test_travel_expense_request_confirmed(self):
        """Test confirming a travel request."""
        self.travel_request.action_request_confirm()
        self.assertEqual(self.travel_request.state, 'confirm')
        self.assertEqual(self.travel_request.confirm_date, date.today())

    def test_travel_expense_request_approved(self):
        """Test approving a confirmed travel request."""
        self.travel_request.action_request_confirm()
        self.travel_request.action_request_approve()
        self.assertEqual(self.travel_request.state, 'approve')
        self.assertEqual(self.travel_request.approve_date, date.today())

    def test_expense_submission_validation(self):
        """Ensure error is raised if no expenses are created before submission."""
        self.travel_request.action_request_confirm()
        self.travel_request.action_request_approve()
        with self.assertRaisesRegex(Exception, "Expense is not created"):
            self.travel_request.action_request_expenses_submitted()

    def test_add_expense_action(self):
        """Test the add expense action returns the correct action dict."""
        action = self.travel_request.action_add_expense()
        self.assertEqual(action['res_model'], 'hr.expense')
        self.assertEqual(action['context']['default_employee_travel_expense_id'], self.travel_request.id)


