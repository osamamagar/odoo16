# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
##############################################################################

from odoo import models, api, fields
import datetime
from datetime import timedelta
import calendar

class HRPayslip(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    salary = fields.Float('Salary')
    

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    summary_id = fields.Many2one('emp.attendance.summary',string='Attendance Summary')
    
    def view_attendance_summary(self):
        if self.summary_id:
            action = self.env.ref('pways_payslip_attendance_sheet.action_emp_attendance_summary').read()[0]
            action['views'] = [(self.env.ref('pways_payslip_attendance_sheet.view_emp_attendance_summary_form').id, 'form')]
            action['res_id'] = self.summary_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        return action
            
            
    def create_attendance_summary(self,payslip):
        attendance_pool =self.env['emp.attendance.summary']
        if payslip.summary_id:
            payslip.summary_id.unlink()
        vals={
            'employee_id':payslip.employee_id.id,
            'from_date':payslip.date_from,
            'to_date':payslip.date_to,
            'company_id':payslip.employee_id.company_id.id,
            'contract_id':payslip.contract_id and payslip.contract_id.id or False,
        }
        summary_id = attendance_pool.create(vals)
        summary_id.action_done()
        payslip.summary_id = summary_id.id
        return True


    @api.onchange('struct_id','date_from', 'date_to')
    def onchange_struct_id(self):
        if self.struct_id:
            if not self.summary_id:
                self.create_attendance_summary(self)

    def compute_sheet(self):
        self.create_attendance_summary(self)
        super(HRPayslip, self).compute_sheet()
        return True
