KB Employee Manager Evaluation Form (Odoo 18)

Flow:
1) HR creates an evaluation form for an employee.
2) Manager is auto-detected from Employee -> Manager (parent_id) and manager's user_id.
3) HR clicks "Send to Manager". Manager gets a chatter notification + activity.
4) Manager opens "Employee Evaluations" menu, fills feedback, clicks "Submit to HR".
5) HR reviews submitted feedback and can mark the record Done.

Setup:
- Give HR users group: "HR - Employee Evaluation"
- Give managers group: "Manager - Employee Evaluation"
- Ensure employee has a manager (Employee form -> Manager) and that manager employee has a linked User.
