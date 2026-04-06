# Labour Cost Allocation

This module handles the automatic allocation of labour costs to projects directly from the Payslip.

## How it works

I have linked the Payslip model to Projects so we can easily attribute costs.

1.  **Payslip Configuration**: On the Payslip form, you'll see a required **Project** field. You must select the project this employee is working on.
2.  **Confirmation**: When you click "Confirm" (or "Compute Sheet" then "Confirm"), the system automatically generates an **Analytic Line**.
    *   It books the `Net Wage` as a cost (negative amount) to the Project's Analytic Account.
    *   If the project doesn't have an Analytic Account linked, it'll stop you with an error.
3.  **Reverting**: If you need to cancel the payslip or set it back to draft, the system is smart enough to remove the analytic entry automatically, so your books stay clean.

## Technical Details

*   **Field Mapping**: I'm using the `account_id` field on the Project to find the analytic account. This seemed to be the standard way to link them.
*   **Validation**: You can't confirm a payslip without a project. This ensures we don't miss any cost allocations.
