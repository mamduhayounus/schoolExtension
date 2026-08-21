from odoo import models, fields

class EnrollmentHistory(models.Model):
    _name = 'enrollment.history'
    _description = 'Student Enrollment History'
    _order = 'transfer_date desc'

    student_id = fields.Many2one('student.student', string="Student", ondelete="cascade")
    transfer_date = fields.Datetime(string="Transfer Date", default=fields.Datetime.now, readonly=True)

    old_code = fields.Char(string="Old Code")
    old_std_id = fields.Char(string="Old Student ID")

    old_institute_id = fields.Many2one('institute.institute', string="Old Institute")
    old_branch_id = fields.Many2one('branch.branch', string="Old Branch")
    old_level_id = fields.Many2one('level.level', string="Old Level")
    old_grade_id = fields.Many2one('grade.grade', string="Old Grade")
    old_section_id = fields.Many2one('section.section', string="Old Section")