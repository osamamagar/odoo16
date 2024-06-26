# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
##############################################################################

{
    'name': 'Employee Attendance Sheet For Payroll',
    'version': '16.0',
    'author': 'Preciseways',
    'category': "Generic Modules/Human Resources",
    'summary': """ Employee attendance sheet for payroll with different types of overtimes and leaves informtion
                Employee overtime managment
                Employeee attenadce summary
                Employee payroll summary
                Employee attendance sheet for payroll
     """,
    'depends': ['hr_contract','hr_attendance', 'pways_hr_payroll_account', 'hr_work_entry_contract'],
    'description':"""Employee attendance sheet for payroll with different types of overtimes and leaves informtion""",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_work_entry_type.xml',
        'views/attendance_summary_view.xml',
        'views/hr_attendance_views.xml',
        ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'price':18.0,
    'currency':'EUR',
    "images":['static/description/banner.png'],
}

