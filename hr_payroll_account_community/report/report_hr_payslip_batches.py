from odoo import api, models


class ReportHrPayslipBatches(models.AbstractModel):
    """Create new model for getting Payslip Details Report"""
    _name = 'report.hr_payroll_account_community.hr_report_payslip_batches'
    _description = 'Payslip Batches Report'


    @api.model
    def _get_report_values(self, docids, data=None):
        runs = self.env['hr.payslip.run'].browse(docids)
        payslip_summary_per_run = {}
        payslip_columns_per_run = {}

        for run in runs:
            # Build dynamic columns from all payslip lines in this run
            code_to_col = {}
            for payslip in run.slip_ids:
                for line in payslip.line_ids:
                    # Use code as key; keep first-seen name and the lowest sequence to sort
                    existing = code_to_col.get(line.code)
                    if existing:
                        if line.sequence < existing['sequence']:
                            existing['sequence'] = line.sequence
                            existing['name'] = line.name
                    else:
                        code_to_col[line.code] = {
                            'code': line.code,
                            'name': line.name,
                            'sequence': line.sequence,
                        }
            # Order columns by sequence then name for consistent display
            columns = sorted(code_to_col.values(), key=lambda c: (c.get('sequence', 0), c.get('name') or ''))
            payslip_columns_per_run[run.id] = columns

            # Build rows (one per payslip) with amounts per code
            slips = []
            for payslip in run.slip_ids:
                currency = payslip.company_id.currency_id
                # map amounts per code for fast lookup in the template
                amounts_by_code = {}
                for line in payslip.line_ids:
                    # If multiple lines share same code, sum them
                    amounts_by_code[line.code] = amounts_by_code.get(line.code, 0.0) + line.total
                slips.append({
                    'employee': payslip.employee_id.name,
                    'amounts': amounts_by_code,
                    'currency': currency,
                })
            payslip_summary_per_run[run.id] = slips

        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip.run',
            'docs': runs,
            'payslip_summary_per_run': payslip_summary_per_run,
            'payslip_columns_per_run': payslip_columns_per_run,
        }

