from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PromoteWizard(models.TransientModel):
    _name = 'promote.wizard'
    _description = 'Batch Student Promotion'

    line_ids = fields.One2many(
        'promote.wizard.line',
        'wizard_id',
        string="Eligible Students"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        enrolled_students = self.env['student.student'].search([
            ('status', '=', 'accept'),
            ('institute_id', '!=', False),
            ('branch_id', '!=', False),
            ('level_id', '!=', False),
            ('grade_id', '!=', False),
        ])

        lines = []
        for student in enrolled_students:
            current_grade_transcripts = student.academic_transcript_ids.filtered(
                lambda t: t.grade_id == student.grade_id
            )
            if not current_grade_transcripts:
                continue

            latest_transcript = current_grade_transcripts.sorted('id', reverse=True)[0]
            if latest_transcript.total_marks < 60:
                continue

            next_grade, next_level, next_branch = self._find_next_academic_step(student)
            if not next_grade:
                continue

            lines.append((0, 0, {
                'student_id': student.id,
                'current_institute_id': student.institute_id.id,
                'current_branch_id': student.branch_id.id,
                'current_level_id': student.level_id.id,
                'current_grade_id': student.grade_id.id,
                'total_marks': latest_transcript.total_marks,
                'next_branch_id': next_branch.id,
                'next_level_id': next_level.id,
                'next_grade_id': next_grade.id,
                'is_selected': True,
            }))

        res['line_ids'] = lines
        return res

    def _find_next_academic_step(self, student):
        """Auto-compute next Grade, Level, and Branch progression strictly"""
        curr_institute = student.institute_id
        curr_branch = student.branch_id
        curr_level = student.level_id
        curr_grade = student.grade_id

        if not (curr_institute and curr_branch and curr_level and curr_grade):
            return False, False, False

        Grade = self.env['grade.grade']
        Level = self.env['level.level']

        grade_order = 'sequence' if 'sequence' in Grade._fields else 'id'
        level_order = 'sequence' if 'sequence' in Level._fields else 'id'

        curr_grade_val = getattr(curr_grade, grade_order, 0)
        curr_level_val = getattr(curr_level, level_order, 0)

        # Step A: Next Grade in current Level
        next_grade = Grade.search([
            ('level_id', '=', curr_level.id),
            (grade_order, '>', curr_grade_val)
        ], order=f'{grade_order} asc', limit=1)

        if next_grade:
            return next_grade, curr_level, curr_branch

        # Step B: Next Level in current Branch
        level_domain = [(level_order, '>', curr_level_val)]
        if 'branch_ids' in Level._fields:
            level_domain.append(('branch_ids', 'in', [curr_branch.id]))

        next_level = Level.search(level_domain, order=f'{level_order} asc', limit=1)

        if next_level:
            first_grade = Grade.search([
                ('level_id', '=', next_level.id)
            ], order=f'{grade_order} asc', limit=1)
            if first_grade:
                return first_grade, next_level, curr_branch

        # Step C: Next Branch in same Institute
        other_branches = self.env['branch.branch'].search([
            ('institute_id', '=', curr_institute.id),
            ('id', '!=', curr_branch.id)
        ])

        for branch in other_branches:
            branch_level_domain = [(level_order, '>', curr_level_val)]
            if 'branch_ids' in Level._fields:
                branch_level_domain.append(('branch_ids', 'in', [branch.id]))

            next_level = Level.search(branch_level_domain, order=f'{level_order} asc', limit=1)

            if next_level:
                first_grade = Grade.search([
                    ('level_id', '=', next_level.id)
                ], order=f'{grade_order} asc', limit=1)
                if first_grade:
                    return first_grade, next_level, branch

        return False, False, False

    def action_promote_students(self):
        """Promote selected students, record audit history, and post chatter notifications"""
        selected_lines = self.line_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            raise ValidationError(_("Please select at least one student to promote."))

        promoted_count = 0
        for line in selected_lines:
            student = line.student_id
            if not student or not line.next_grade_id:
                continue

            # 1. Audit history snapshot
            self.env['enrollment.history'].create({
                'student_id': student.id,
                'old_code': student.code,
                'old_std_id': student.std_id,
                'old_institute_id': student.institute_id.id if student.institute_id else False,
                'old_branch_id': student.branch_id.id if student.branch_id else False,
                'old_level_id': student.level_id.id if student.level_id else False,
                'old_grade_id': student.grade_id.id if student.grade_id else False,
                'old_section_id': student.section_id.id if student.section_id else False,
            })

            # 2. Update placement
            student.write({
                'branch_id': line.next_branch_id.id,
                'level_id': line.next_level_id.id,
                'grade_id': line.next_grade_id.id,
                'section_id': False,
            })

            # 3. Chatter notification
            chatter_msg = f"""Batch Student Promotion by {self.env.user.name}
• Student: {student.display_name}
• Branch: {line.current_branch_id.display_name if line.current_branch_id else 'None'} ➔ {line.next_branch_id.display_name if line.next_branch_id else 'None'}
• Level: {line.current_level_id.display_name if line.current_level_id else 'None'} ➔ {line.next_level_id.display_name if line.next_level_id else 'None'}
• Grade: {line.current_grade_id.display_name if line.current_grade_id else 'None'} ➔ {line.next_grade_id.display_name if line.next_grade_id else 'None'}"""

            student.message_post(body=chatter_msg)
            promoted_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Promotion Completed'),
                'message': _('%d students have been successfully promoted!') % promoted_count,
                'type': 'success',
                'sticky': False,
            }
        }


class PromoteWizardLine(models.TransientModel):
    _name = 'promote.wizard.line'
    _description = 'Batch Student Promotion Line'

    wizard_id = fields.Many2one('promote.wizard', ondelete='cascade')
    is_selected = fields.Boolean(string="Promote?", default=True)
    student_id = fields.Many2one('student.student', string="Student", readonly=True)
    total_marks = fields.Float(string="Total Marks", readonly=True)

    current_institute_id = fields.Many2one('institute.institute', string="Institute", readonly=True)
    current_branch_id = fields.Many2one('branch.branch', string="Current Branch", readonly=True)
    current_level_id = fields.Many2one('level.level', string="Current Level", readonly=True)
    current_grade_id = fields.Many2one('grade.grade', string="Current Grade", readonly=True)

    next_branch_id = fields.Many2one('branch.branch', string="Next Branch", required=True)
    next_level_id = fields.Many2one('level.level', string="Next Level", required=True)
    next_grade_id = fields.Many2one('grade.grade', string="Next Grade", required=True)