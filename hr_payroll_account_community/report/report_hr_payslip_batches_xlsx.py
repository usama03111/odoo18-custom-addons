from odoo import models


class ReportHrPayslipBatchesXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_account_community.payslip_batches_xlsx'
    _description = 'Payslip Batches XLSX'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, docs):
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': 'yellow'})
        money = workbook.add_format({'num_format': '#,##0.00'})

        for run in docs:
            sheet = workbook.add_worksheet((run.name or 'Batch')[:31])
            row = 0

            # Title
            sheet.write(row, 0, 'Name', bold)
            sheet.write(row+1, 0, run.name or '', )
            sheet.write(row, 1, 'Start Date', bold)
            sheet.write(row+1, 1, str(run.date_start),)
            sheet.write(row, 2, 'End Date', bold)
            sheet.write(row+1, 2, str(run.date_end),)
            row += 3

            # Build dynamic columns like in PDF
            code_to_col = {}
            for payslip in run.slip_ids:
                for line in payslip.line_ids:
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
            columns = sorted(code_to_col.values(), key=lambda c: (c.get('sequence', 0), c.get('name') or ''))

            # --- Step 1: Calculate max widths ---
            col_widths = {'Employee': len('Employee'), 'Bank Account': len('Bank Account')}
            for column in columns:
                header = column.get('name') or column.get('code')
                col_widths[column['code']] = len(header)

            for payslip in run.slip_ids:
                # Employee column
                emp_name = payslip.employee_id.name or ''
                col_widths['Employee'] = max(col_widths['Employee'], len(emp_name))
                
                # Bank Account column
                bank_account = payslip.employee_id.bank_account_id.acc_number if payslip.employee_id.bank_account_id else ''
                col_widths['Bank Account'] = max(col_widths['Bank Account'], len(bank_account))

                # Each line column
                for line in payslip.line_ids:
                    value_str = f"{line.total:,.2f}"
                    col_widths[line.code] = max(col_widths.get(line.code, 0), len(value_str))

            # --- Step 2: Write headers ---
            col = 0
            sheet.write(row, col, 'Employee', bold)
            sheet.set_column(col, col, col_widths['Employee'] + 2)  # adjust width
            col += 1
            sheet.write(row, col, 'Bank Account', bold)
            sheet.set_column(col, col, col_widths['Bank Account'] + 2)  # adjust width
            col += 1
            for column in columns:
                header = column.get('name') or column.get('code')
                sheet.write(row, col, header, bold)
                sheet.set_column(col, col, col_widths[column['code']] + 2)  # adjust width
                col += 1
            row += 1

            # --- Step 3: Write data rows ---
            for payslip in run.slip_ids:
                amounts_by_code = {}
                for line in payslip.line_ids:
                    amounts_by_code[line.code] = amounts_by_code.get(line.code, 0.0) + line.total

                col = 0
                sheet.write(row, col, payslip.employee_id.name or '')
                col += 1
                bank_account = payslip.employee_id.bank_account_id.acc_number if payslip.employee_id.bank_account_id else ''
                sheet.write(row, col, bank_account)
                col += 1
                for column in columns:
                    value = amounts_by_code.get(column['code'], 0.0)
                    sheet.write_number(row, col, value, money)
                    col += 1
                row += 1