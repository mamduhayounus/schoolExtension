from odoo import models, api, fields

class AdmissionExtension(models.Model):
    _inherit = "admission.admission"
    _description = "Admission Extension"

    hobby=fields.Char(string = 'Hobby')

