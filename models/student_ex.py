from lxml import etree
from odoo import models, fields, api

class Student(models.Model):
    _inherit = 'student.student'

    enrollment_history_ids = fields.One2many(
        'enrollment.history',
        'student_id',
        string="Enrollment History"
    )
    academic_transcript_ids = fields.One2many(
        'academic.transcript',
        'student_id',
        string="Academic Transcripts"
    )

    weight = fields.Float(string="Weight (kg)")
    height = fields.Float(string="Height (cm)")

    status = fields.Selection(selection_add=[('left', 'Left')], ondelete={'left': 'cascade'})
    leave_date = fields.Date(string='Leaving Date', readonly=True)
    due_payment = fields.Float(string='Due Payment', default=0.0)
    dues = fields.Float(string='Dues', default=0.0)

    enrollment_history_count = fields.Integer(
        string="Enrollment History Count",
        compute='_compute_smart_button_counts'
    )
    academic_transcript_count = fields.Integer(
        string="Transcript Count",
        compute='_compute_smart_button_counts'
    )

    is_view_hidden = fields.Boolean(
        string="View Hidden",
        default=False,
        store=True
    )


    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        if 'form' in res['views']:
            doc = etree.XML(res['views']['form']['arch'])

            # Preserve parent context in child lists for readonly fields
            for node in doc.xpath("//field[@readonly]"):
                cond = node.get('readonly', '')
                if "parent.status" in cond:
                    node.set('readonly', "parent.status in ['accept', 'reject', 'left']")
                elif "status" in cond:
                    node.set('readonly', "status in ['accept', 'reject', 'left']")

            res['views']['form']['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.depends('enrollment_history_ids', 'academic_transcript_ids')
    def _compute_smart_button_counts(self):
        for student in self:
            student.enrollment_history_count = len(student.enrollment_history_ids)
            student.academic_transcript_count = len(student.academic_transcript_ids)

    def action_view_enrollment_history(self):
        self.ensure_one()
        return {
            'name': _('Enrollment History'),
            'type': 'ir.actions.act_window',
            'res_model': 'enrollment.history',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_academic_transcripts(self):
        self.ensure_one()
        return {
            'name': _('Academic Performance Transcripts'),
            'type': 'ir.actions.act_window',
            'res_model': 'academic.transcript',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }