# -*- coding: utf-8 -*-
# Part of Preciseways. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    slip_ids = fields.One2many('hr.payslip', 'employee_id', string='Payslips', readonly=True)
    payslip_count = fields.Integer(compute='_compute_payslip_count', string='Payslip Count', groups="pways_hr_payroll.group_hr_payroll_user")

    def _compute_payslip_count(self):
        for employee in self:
            employee.payslip_count = len(employee.slip_ids)



from odoo import models, fields

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    worked_day_id = fields.Many2one('hr.payslip.worked_days', string='Worked Day')
