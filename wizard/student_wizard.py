from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StudentWizard(models.TransientModel):
    _name = 'student.wizard'
    _description = 'Update Student Academic Information'

    student_id = fields.Many2one('student.student', string="Student", required=True)
    institute_id = fields.Many2one('institute.institute', string="Institute", required=True)
    branch_id = fields.Many2one('branch.branch', string="Branch", required=True)
    level_id = fields.Many2one('level.level', string="Level", required=True)
    grade_id = fields.Many2one('grade.grade', string="Grade", required=True)
    section_id = fields.Many2one('section.section', string="Section", required=True)

    # NEW FIELDS FOR DYNAMIC STUDENT ID
    current_institute_id = fields.Many2one('institute.institute', string="Current Institute")
    is_institute_changed = fields.Boolean(compute='_compute_is_institute_changed', store=True)
    new_std_id = fields.Char(string="New Student ID")

    @api.depends('institute_id', 'current_institute_id')
    def _compute_is_institute_changed(self):
        for rec in self:
            if rec.institute_id and rec.current_institute_id:
                rec.is_institute_changed = rec.institute_id != rec.current_institute_id
            else:
                rec.is_institute_changed = False

    @api.model
    def default_get(self, fields_list):
        """ Pre-fill fields from the current student record """
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')

        if active_id:
            student = self.env['student.student'].browse(active_id)

            if student.status != 'accept':
                raise ValidationError(_("Academic information can only be updated for Enrolled students!"))

            res.update({
                'student_id': student.id,
                'institute_id': student.institute_id.id if student.institute_id else False,
                'current_institute_id': student.institute_id.id if student.institute_id else False, # Capture current institute
                'branch_id': student.branch_id.id if student.branch_id else False,
                'level_id': student.level_id.id if student.level_id else False,
                'grade_id': student.grade_id.id if student.grade_id else False,
                'section_id': student.section_id.id if student.section_id else False,
            })
        return res

    @api.onchange('institute_id')
    def _onchange_institute_id(self):
        if not self.institute_id or (self.branch_id and self.branch_id.institute_id != self.institute_id):
            self.branch_id = False
            self.level_id = False
            self.grade_id = False
            self.section_id = False

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if not self.branch_id or (self.level_id and self.branch_id not in self.level_id.branch_ids):
            self.level_id = False
            self.grade_id = False
            self.section_id = False

    @api.onchange('level_id')
    def _onchange_level_id(self):
        if not self.level_id or (self.grade_id and self.grade_id.level_id != self.level_id):
            self.grade_id = False
            self.section_id = False

    @api.onchange('grade_id')
    def _onchange_grade_id(self):
        if not self.grade_id or (self.section_id and self.grade_id not in self.section_id.grade_ids):
            self.section_id = False

    # --- ACTION SUBMIT VALIDATION & UPDATE ---
    def action_update_academic_info(self):
        self.ensure_one()
        student = self.student_id
        # 1. Check for zero changes
        if (self.institute_id == student.institute_id and
                self.branch_id == student.branch_id and
                self.level_id == student.level_id and
                self.grade_id == student.grade_id and
                self.section_id == student.section_id):
            raise ValidationError(_("No changes detected. The selected academic details are identical to current ones."))

        # 2. Capture "Before" snapshot for the Chatter Log and History
        old_institute = student.institute_id
        old_branch = student.branch_id
        old_level = student.level_id
        old_grade = student.grade_id
        old_section = student.section_id
        old_code = student.code
        old_std_id = student.std_id

        # 3. Prepare values for update
        vals = {
            'institute_id': self.institute_id.id,
            'branch_id': self.branch_id.id,
            'level_id': self.level_id.id,
            'grade_id': self.grade_id.id,
            'section_id': self.section_id.id if self.section_id else False,
        }

        # 4. DYNAMIC SEQUENCE GENERATION & HISTORY (Institute Change)
        if self.institute_id.id != old_institute.id:
            institute = self.institute_id

            # --- A. CREATE ENROLLMENT HISTORY RECORD ---
            self.env['enrollment.history'].create({
                'student_id': student.id,
                'old_code': old_code,
                'old_std_id': student.std_id,
                'old_institute_id': old_institute.id,
                'old_branch_id': old_branch.id,
                'old_level_id': old_level.id,
                'old_grade_id': old_grade.id,
                'old_section_id': old_section.id if old_section else False,
            })

            # --- B. GENERATE NEW SEQUENCE CODE & SET NEW STD_ID ---
            if hasattr(institute, 'code') and institute.code:
                clean_code = institute.code.strip().upper()
                seq_code = f"student.sequence.{clean_code.lower()}"

                Sequence = self.env['ir.sequence'].sudo()
                generated_code = Sequence.next_by_code(seq_code)

                vals['code'] = generated_code
            else:
                vals['code'] = self.env['ir.sequence'].sudo().next_by_code('student.student') or 'New'

        # 5. Apply changes to Student
        student.write(vals)

        chatter_msg = f"""Academic Information Updated by {self.env.user.name}
            • Student Code: {old_code} ➔ {student.code}
            • Student ID: {old_std_id or 'None'} ➔ {student.std_id or 'None'}
            • Institute: {old_institute.display_name if old_institute else 'None'} ➔ {self.institute_id.display_name if self.institute_id else 'None'}
            • Branch: {old_branch.display_name if old_branch else 'None'} ➔ {self.branch_id.display_name if self.branch_id else 'None'}
            • Level: {old_level.display_name if old_level else 'None'} ➔ {self.level_id.display_name if self.level_id else 'None'}
            • Grade: {old_grade.display_name if old_grade else 'None'} ➔ {self.grade_id.display_name if self.grade_id else 'None'}
            • Section: {old_section.display_name if old_section else 'None'} ➔ {self.section_id.display_name if self.section_id else 'None'}"""

        student.message_post(body=chatter_msg)

        return {'type': 'ir.actions.act_window_close'}