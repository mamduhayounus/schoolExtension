from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LeaveWizard(models.TransientModel):
    _name = 'leave.wizard'
    _description = 'Student Leave Clearance Wizard'

    student_id = fields.Many2one('student.student', string='Select Student', required=True)
    institute_id = fields.Many2one(related='student_id.institute_id', string='Institute', readonly=True)
    branch_id = fields.Many2one(related='student_id.branch_id', string='Branch', readonly=True)
    grade_id = fields.Many2one(related='student_id.grade_id', string='Grade', readonly=True)
    level_id = fields.Many2one(related='student_id.level_id', string='Level', readonly=True)
    due_payment = fields.Float(related='student_id.due_payment', string='Outstanding Dues', readonly=True)
    leave_date = fields.Date(string='Leave Date', default=fields.Date.today, required=True)
    reason = fields.Text(string='Reason for Leaving')

    def action_process_leave(self):
        if self.due_payment > 0:
            raise ValidationError(
                f"Cannot process leave! Student has outstanding dues of {self.due_payment:.2f}."
            )

        self.student_id.write({
            'status': 'left',
            'leave_date': self.leave_date,
        })

        self.env['student.leave'].create({
            'student_id': self.student_id.id,
            'leave_date': self.leave_date,
            'reason': self.reason,
        })

        return {'type': 'ir.actions.act_window_close'}