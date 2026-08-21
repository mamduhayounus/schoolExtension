from odoo import models, fields

class StudentLeave(models.Model):
    _name = 'student.leave'
    _description = 'Student Leave Record'
    _rec_name = 'student_id'

    student_id = fields.Many2one('student.student', string='Student', required=True, readonly=True)
    leave_date = fields.Date(string='Leave Date', required=True, readonly=True)
    institute_id = fields.Many2one(related='student_id.institute_id', string='Institute', readonly=True)
    branch_id = fields.Many2one(related='student_id.branch_id', string='Branch', readonly=True)
    grade_id = fields.Many2one(related='student_id.grade_id', string='Grade', readonly=True)
    level_id = fields.Many2one(related='student_id.level_id', string='Level', readonly=True)
    reason = fields.Text(string='Leave Reason')