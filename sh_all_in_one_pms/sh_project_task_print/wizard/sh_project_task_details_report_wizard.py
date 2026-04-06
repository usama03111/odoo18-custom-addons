# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models
import xlwt
import base64
from io import BytesIO
from odoo.tools import html2plaintext


class ShProjectTaskDetailsReportWizard(models.TransientModel):
    _name = "sh.project.task.details.report.wizard"
    _description = 'Project Task details report wizard model'

    def print_task_xls_report(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center, vertical center;borders:top thick;borders:bottom thick;')
        bold = xlwt.easyxf(
            'font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        format1 = xlwt.easyxf(
            'font:height 200,bold True;align:vertical center;')
        format2 = xlwt.easyxf('font:height 200;align:vertical center;')
        label = xlwt.easyxf(
            'font:height 250,bold True;pattern: pattern solid, fore_colour white;align: horiz center,vertical center;borders:top thick;borders:bottom thick;')

        data = {}
        data = dict(data or {})
        active_ids = self.env.context.get('active_ids')

        Tasks = self.env['project.task'].search(
            [('id', 'in', active_ids)])
        NO = 0
        for task in Tasks:

            NO += 1
            child_lines = []
            timesheet_lines = []
            final_value = {}
            users = []
            heading = task.name + \
                ' ( ' + task.stage_id.name if task.stage_id.name else '' + ' )'
            progress = str(task.progress) + ' %'
            subtask_allocated_hours = str(
                task.subtask_allocated_hours) + ' planned hours'

            final_value['name'] = heading
            final_value['project_id'] = task.project_id.name
            final_value['partner_id'] = task.partner_id.display_name
            final_value['date_assign'] = task.date_assign
            final_value['email_cc'] = task.email_cc
            final_value['date_deadline'] = task.date_deadline
            if task.description:
                final_value['description'] = html2plaintext(task.description)
            final_value['allocated_hours'] = str(task.allocated_hours)
            final_value['progress'] = task.progress
            final_value['subtask_allocated_hours'] = subtask_allocated_hours
            final_value['effective_hours'] = task.effective_hours
            final_value['remaining_hours'] = task.remaining_hours

            for user in task.user_ids:
                users.append(user.name)

            final_value['user_ids'] = ','.join(users)

            for child in task.child_ids:
                child_users = []
                product = {
                    'name': child.name,
                    'date_assign': child.date_assign,
                    'date_deadline': child.date_deadline,
                    'stage_id': child.stage_id.name,
                }

                for user in child.user_ids:
                    child_users.append(user.name)

                product['user_ids'] = ','.join(child_users)
                child_lines.append(product)

            for timesheet in task.timesheet_ids:
                record = {
                    'date': timesheet.date,
                    'employee_id': timesheet.employee_id.name,
                    'name': timesheet.name,
                    'unit_amount': timesheet.unit_amount,
                }

                timesheet_lines.append(record)

            Name = 'Sheet ' + str(NO) + ' - ' + str(task.name)

            worksheet = workbook.add_sheet(
                str(Name), cell_overwrite_ok=True)

            worksheet.write_merge(
                0, 1, 0, 4, final_value['name'], heading_format)

            worksheet.col(0).width = int(32 * 260)
            worksheet.col(1).width = int(32 * 260)
            worksheet.col(2).width = int(32 * 260)
            worksheet.col(3).width = int(32 * 260)
            worksheet.col(4).width = int(32 * 260)

            worksheet.write_merge(3, 4, 0, 0, "Project Name:", format1)
            if final_value['project_id']:
                worksheet.write_merge(
                    3, 4, 1, 1, final_value['project_id'], format2)
            else:
                worksheet.write_merge(3, 4, 1, 1, '', format2)
            worksheet.write_merge(3, 4, 3, 3, "Assign To:", format1)
            if final_value['user_ids']:
                worksheet.write_merge(
                    3, 4, 4, 4, final_value['user_ids'], format2)
            else:
                worksheet.write_merge(3, 4, 4, 4, '', format2)

            worksheet.write_merge(5, 6, 0, 0, "Customer Name:", format1)
            if final_value['partner_id']:
                worksheet.write_merge(
                    5, 6, 1, 1, final_value['partner_id'], format2)
            else:
                worksheet.write_merge(5, 6, 1, 1, '', format2)
            worksheet.write_merge(5, 6, 3, 3, "Assign Date:", format1)
            if final_value['date_assign']:
                worksheet.write_merge(
                    5, 6, 4, 4, str(final_value['date_assign']), format2)
            else:
                worksheet.write_merge(5, 6, 4, 4, '', format2)

            worksheet.write_merge(7, 8, 0, 0, "Customer Email:", format1)
            if final_value['email_cc']:
                worksheet.write_merge(
                    7, 8, 1, 1, final_value['email_cc'], format2)
            else:
                worksheet.write_merge(7, 8, 1, 1, '', format2)
            worksheet.write_merge(7, 8, 3, 3, "Deadline Date:", format1)
            if final_value['date_deadline']:
                worksheet.write_merge(
                    7, 8, 4, 4, str(final_value['date_deadline']), format2)
            else:
                worksheet.write_merge(7, 8, 4, 4, '', format2)

            row = 10

            if task.description:
                worksheet.write_merge(row, row+1, 0, 4, "Description", label)
                row += 2

                worksheet.write_merge(
                    row, row+4, 0, 4, final_value['description'], format2)
                row += 6

            if task.child_ids:
                worksheet.write_merge(row, row+1, 0, 4, "Sub Tasks", label)
                row += 2
                worksheet.write(row, 0, "Task", bold)
                worksheet.write(row, 1, "Assign To", bold)
                worksheet.write(row, 2, "Assign Date", bold)
                worksheet.write(row, 3, "Deadline", bold)
                worksheet.write(row, 4, "Stage", bold)

                row += 1

                for rec in child_lines:

                    if rec.get('name'):
                        worksheet.write(row, 0, rec.get('name'))
                    if rec.get('user_ids'):
                        worksheet.write(row, 1, rec.get('user_ids'))
                    if rec.get('date_assign'):
                        worksheet.write(row, 2, str(rec.get('date_assign')))
                    if rec.get('date_deadline'):
                        worksheet.write(row, 3, str(rec.get('date_deadline')))
                    if rec.get('stage_id'):
                        worksheet.write(row, 4, rec.get('stage_id'))
                    row += 1
                row += 2

            if task.allocated_hours:

                worksheet.write_merge(row, row+1, 0, 4, "Timesheets", label)
                row += 2

                worksheet.write_merge(
                    row, row+1, 0, 0, "Planned Hours:", format1)
                if final_value['allocated_hours']:
                    worksheet.write_merge(
                        row, row+1, 1, 1, final_value['allocated_hours'], format2)
                else:
                    worksheet.write_merge(row, row+1, 1, 1, '', format2)
                worksheet.write_merge(row, row+1, 3, 3, "Progress:", format1)
                if progress:
                    worksheet.write_merge(
                        row, row+1, 4, 4, progress, format2)
                else:
                    worksheet.write_merge(row, row+1, 4, 4, '', format2)
                row += 2

                worksheet.write_merge(row, row+1, 0, 0, "Sub Tasks:", format1)
                if final_value['subtask_allocated_hours']:
                    worksheet.write_merge(
                        row, row+1, 1, 1, final_value['subtask_allocated_hours'], format2)
                else:
                    worksheet.write_merge(row, row+1, 1, 1, '', format2)
                row += 3

                worksheet.write(row, 0, "Date", bold)
                worksheet.write(row, 1, "Employee", bold)
                worksheet.write(row, 2, "Description", bold)
                worksheet.write(row, 3, "Duration ( in hours )", bold)

                row += 1

                for rec in timesheet_lines:

                    if rec.get('date'):
                        worksheet.write(row, 0, str(rec.get('date')))
                    if rec.get('employee_id'):
                        worksheet.write(row, 1, rec.get('employee_id'))
                    if rec.get('name'):
                        worksheet.write(row, 2, rec.get('name'))
                    if rec.get('unit_amount'):
                        worksheet.write(row, 3, str(rec.get('unit_amount')))

                    row += 1

        filename = ('Project Task Detail Xls Report' + '.xls')
        fp = BytesIO()
        workbook.save(fp)
        export_id = self.env['project.task.detail.excel.extended'].sudo().create({
            'excel_file': base64.encodebytes(fp.getvalue()),
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=project.task.detail.excel.extended&field=excel_file&download=true&id=%s&filename=%s' % (export_id.id, export_id.file_name),
            'target': 'new',
        }
