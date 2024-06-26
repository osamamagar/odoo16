# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
##############################################################################

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

class resource_calendar_attendance(models.Model):
    _inherit = 'resource.calendar.attendance'
    
    break_hour = fields.Float('Break Hour')
    
    
class resource_calendar(models.Model):
    _inherit = 'resource.calendar'
    
    normal_day_overtime = fields.Float('Normal Day Overtime', default=1.125, digits='Account')
    off_day_overtime = fields.Float('Week Off Day Overtime', default=1.25, digits='Account')
    holiday_overtime = fields.Float('Pub Holiday Overtime', default=1.75, digits='Account')
    

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overtime_schedule = fields.Float(string='Overtime Schedual', related='company_id.overtime_schedule')


class hr_attendance(models.Model):
    _inherit = 'hr.attendance'
    
    rest_day = fields.Boolean('Rest Day')
    worked_days_id = fields.Many2one('hr.payslip.worked_days', string='Worked Days')

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    wage_by = fields.Selection(selection=[('fixed', 'Fixed Wage'),('by_hours', 'Wage by Working Hours')],string="Wage", default='fixed', required="1")                
    wage_by_hours = fields.Float(string="Wage")
    work_type = fields.Selection(selection=[('full_time', 'Full Time'),('part_time', 'Part Time')],string="Work Type", default='full_time')

class res_company(models.Model):
    _inherit = 'res.company'

    overtime_schedule = fields.Float(string='Overtime Schedual', default="0.5")
    
    @api.onchange('overtime_schedule')
    def onchange_overtime_schedule(self):
        if self.overtime_schedule and self.overtime_schedule < 0.0:
            raise ValidationError(_("Overtime Schedule Must be Zero or Positive"))

