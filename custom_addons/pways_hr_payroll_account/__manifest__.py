# -*- coding: utf-8 -*-
# Part of Preciseways. See LICENSE file for full copyright and licensing details.


{
    'name': 'HR Payroll Accounting Community Edition',
    "version" : "16.0.0.1",
    'category': 'Generic Modules/Human Resources',
    'license': 'OPL-1',
    'summary': 'Odoo HR Payroll Community Payroll',
    'description' :"""
        
        Generic Payroll System Integrated with Accounting in odoo,
        Manage your employee payroll records in odoo,
        HR Payroll Accounting module in odoo,
        Easy to create employee payslip in odoo,
        Manage your employee payroll or payslip records in odoo,
        Generating journal entry in odoo,
        Managing Entries in Accounting Journals in odoo,
    
    """,
    "author": "Preciseways",
    "website" : "https://www.preciseways.com",
    'depends': ['pways_hr_payroll', 'account'],
    'data': ['views/hr_payroll_account_views.xml'],
    'demo': ['data/hr_payroll_account_demo.xml'],
    'test': ['../account/test/account_minimal_test.xml'],
    "auto_install": False,
    "installable": True,
    "images":['static/description/banner.png'],

}
