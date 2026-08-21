from odoo import models, fields, api

class AcademicTranscript(models.Model):
    _name = 'academic.transcript'
    _description = 'Academic Performance Transcript'

    student_id = fields.Many2one('student.student', string="Student", ondelete="cascade")
    grade_id = fields.Many2one('grade.grade', string="Grade", compute='_compute_student_info', store=True, readonly=True)
    section_id = fields.Many2one('section.section', string="Section", compute='_compute_student_info', store=True, readonly=True)

    first_marks = fields.Float(string="First Term Marks")
    mid_marks = fields.Float(string="Mid Term Marks")
    second_marks = fields.Float(string="Second Term Marks")
    final_marks = fields.Float(string="Final Marks")
    total_marks = fields.Float(string="Total Marks", compute='_compute_total_marks', store=True)

    @api.depends('first_marks', 'mid_marks', 'second_marks', 'final_marks')
    def _compute_total_marks(self):
        for rec in self:
            rec.total_marks = rec.first_marks + rec.mid_marks + rec.second_marks + rec.final_marks

    @api.depends('student_id')
    def _compute_student_info(self):
        for rec in self:
            if rec.student_id:
                rec.grade_id = rec.student_id.grade_id
                rec.section_id = rec.student_id.section_id