{
    'name': 'School Extension',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'author': 'Mamduha Younus',
    'depends': ['base', 'school'],
    'data': [
        'security/ir.model.access.csv',  # Put this back at the top
        'views/student_ex.xml',
        'views/admission_ex.xml',
        'wizard/student_wizard.xml',
        'wizard/promote_wizard.xml',
        'wizard/print_wizard.xml',
        'wizard/leave_wizard.xml',
        'report/summary_report.xml',
        'report/report.xml',
    ],
    'installable': True,
    'application': True,
}