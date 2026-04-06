# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models
import xlwt
import base64
from io import BytesIO


class ShProjectDetailsReportWizard(models.TransientModel):
    _name = "sh.project.details.report.wizard"
    _description = 'Project details report wizard model'

    def print_project_xls_report(self):
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
        Projects = self.env['project.project'].search(
            [('id', 'in', active_ids)])
        NO = 0

        for project in Projects:
            NO += 1
            task_lines = []
            final_value = {}

            final_value['name'] = project.name
            final_value['user_id'] = project.user_id.name
            final_value['partner_id'] = project.partner_id.display_name
            final_value['label_tasks'] = project.label_tasks

            for lines in project.task_ids:
                users = []
                product = {
                    'name': lines.name,
                    'allocated_hours': lines.allocated_hours,
                    'effective_hours': lines.effective_hours,
                    'remaining_hours': lines.remaining_hours,
                    'date_assign': lines.date_assign,
                    'date_deadline': lines.date_deadline,
                    'stage_id': lines.stage_id,
                }
                for user in lines.user_ids:
                    # print('user:',user)
                    users.append(user.name)
                    # print('users:',users)
                    # print('name:',user.name)

                product['user_ids'] = ','.join(users)
                task_lines.append(product)

            Name = 'Sheet ' + str(NO) + ' - ' + str(project.name)

            worksheet = workbook.add_sheet(
                str(Name), cell_overwrite_ok=True)

            worksheet.write_merge(
                0, 1, 0, 7, final_value['name'], heading_format)

            worksheet.col(0).width = int(40 * 260)
            worksheet.col(1).width = int(14 * 260)
            worksheet.col(2).width = int(14 * 260)
            worksheet.col(3).width = int(17 * 260)
            worksheet.col(4).width = int(27 * 260)
            worksheet.col(5).width = int(19 * 260)
            worksheet.col(6).width = int(18 * 260)
            worksheet.col(7).width = int(15 * 260)

            worksheet.write_merge(3, 4, 0, 0, "Project Manager:", format1)
            worksheet.write_merge(3, 4, 1, 1, final_value['user_id'], format2)
            worksheet.write_merge(3, 4, 5, 5, "Customer:", format1)
            if final_value['partner_id']:
                worksheet.write_merge(
                    3, 4, 6, 6, final_value['partner_id'], format2)
            else:
                worksheet.write_merge(3, 4, 6, 6, '', format2)

            worksheet.write_merge(
                6, 7, 0, 7, final_value['label_tasks'], label)

            worksheet.write(9, 0, "Task Name", bold)
            worksheet.write(9, 1, "Planned Hours", bold)
            worksheet.write(9, 2, "Spent Hours", bold)
            worksheet.write(9, 3, "Remaining Hours", bold)
            worksheet.write(9, 4, "Assign To", bold)
            worksheet.write(9, 5, "Assign Date", bold)
            worksheet.write(9, 6, "Deadline", bold)
            worksheet.write(9, 7, "Stage", bold)

            row = 10

            for rec in task_lines:
                if rec.get('name'):
                    worksheet.write(row, 0, rec.get('name'))
                if rec.get('allocated_hours'):
                    worksheet.write(row, 1, str(rec.get('allocated_hours')))
                if rec.get('effective_hours'):
                    worksheet.write(row, 2, str(rec.get('effective_hours')))
                if rec.get('remaining_hours'):
                    worksheet.write(row, 3, str(rec.get('remaining_hours')))
                if rec.get('user_ids'):
                    worksheet.write(row, 4, rec.get('user_ids'))
                if rec.get('date_assign'):
                    worksheet.write(row, 5, str(rec.get('date_assign')))
                if rec.get('date_deadline'):
                    worksheet.write(row, 6, str(rec.get('date_deadline')))
                if rec.get('stage_id'):
                    worksheet.write(row, 7, str(rec.get('stage_id').name))

                row += 1

        filename = ('Project Detail Xls Report' + '.xls')
        print(filename)
        fp = BytesIO()
        print(fp)
        workbook.save(fp)
        export_id = self.env['project.detail.excel.extended'].sudo().create({
            'excel_file': base64.encodebytes(fp.getvalue()),
            'file_name': filename,
        })
        print(export_id)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=project.detail.excel.extended&field=excel_file&download=true&id=%s&filename=%s' % (export_id.id, export_id.file_name),
            'target': 'new',
        }
