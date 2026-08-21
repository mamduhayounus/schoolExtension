import base64
import io
import xlsxwriter
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PrintWizard(models.TransientModel):
    _name = 'print.wizard'
    _description = 'Print Students Summary Wizard'

    institute_ids = fields.Many2many('institute.institute', string='Institutes')
    branch_ids = fields.Many2many('branch.branch', string='Branches')
    grade_ids = fields.Many2many('grade.grade', string='Grades')
    level_ids = fields.Many2many('level.level', string='Levels')

    line_ids = fields.One2many('print.wizard.line', 'wizard_id', string='Students List')
    total_students = fields.Integer(string='Total Students', compute='_compute_total_students', store=True)

    @api.depends('line_ids')
    def _compute_total_students(self):
        for record in self:
            record.total_students = len(record.line_ids)

    def _get_filtered_students(self):
        if not any([self.institute_ids, self.branch_ids, self.level_ids, self.grade_ids]):
            raise ValidationError("Please select at least one Institute, Branch, Level, or Grade.")

        domain = []
        if self.institute_ids:
            domain.append(('institute_id', 'in', self.institute_ids.ids))
        if self.branch_ids:
            domain.append(('branch_id', 'in', self.branch_ids.ids))
        if self.level_ids:
            domain.append(('level_id', 'in', self.level_ids.ids))
        if self.grade_ids:
            domain.append(('grade_id', 'in', self.grade_ids.ids))

        return self.env['student.student'].search(domain)

    def action_print_report(self):
        students = self._get_filtered_students()
        lines = []
        for index, student in enumerate(students, start=1):
            lines.append((0, 0, {
                'sr_no': index,
                'student_id': student.id,
            }))
        self.line_ids = [(5, 0, 0)] + lines
        return self.env.ref('school_extension.action_report_student_summary').report_action(self)

    def action_export_excel(self):
        students = self._get_filtered_students()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Student Summary')

        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#cfcfcf', 'font_color': '#5e3b69',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left'})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})

        headers = ['SR. NO.', 'NAME', 'STATUS', 'INSTITUTE', 'BRANCH', 'GRADE']
        for col_idx, header in enumerate(headers):
            worksheet.write(0, col_idx, header, header_format)

        status_selection = self.env['student.student'].fields_get(['status'])['status']['selection']
        status_labels = dict(status_selection)

        for row_idx, student in enumerate(students, start=1):
            worksheet.write(row_idx, 0, row_idx, center_format)
            worksheet.write(row_idx, 1, student.name or '', cell_format)

            status_val = status_labels.get(student.status, '')
            worksheet.write(row_idx, 2, status_val, center_format)

            worksheet.write(row_idx, 3, student.institute_id.name , cell_format)
            worksheet.write(row_idx, 4, student.branch_id.name , cell_format)
            worksheet.write(row_idx, 5, student.grade_id.name , cell_format)

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:F', 22)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Student_Summary.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class PrintWizardLine(models.TransientModel):
    _name = 'print.wizard.line'
    _description = 'Print Student Wizard Line'

    wizard_id = fields.Many2one('print.wizard', string='Wizard', ondelete='cascade')
    sr_no = fields.Integer(string='SR. No.')
    student_id = fields.Many2one('student.student', string='Student', required=True)

    status = fields.Selection(related='student_id.status', string='Status', readonly=True)
    institute_id = fields.Many2one(related='student_id.institute_id', string='Institute', readonly=True)
    branch_id = fields.Many2one(related='student_id.branch_id', string='Branch', readonly=True)
    grade_id = fields.Many2one(related='student_id.grade_id', string='Grade', readonly=True)
    level_id = fields.Many2one(related='student_id.level_id', string='Level', readonly=True)