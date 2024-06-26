# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
##############################################################################

from odoo import models, fields, api
from datetime import datetime
import calendar
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
import pytz

def to_naive_user_tz(datetime, record):
    tz_name = record._context.get('tz') or record.env.user.tz
    tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
    return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(tz).replace(tzinfo=None)
    
class employee_attendance_summary(models.Model):
    _name = 'emp.attendance.summary'
    _rec_name='employee_id'
    _order = 'id desc'
    
    @api.model
    def _get_from_date(self):
        date = datetime.now()
        month = date.month
        if date.month < 10:
            month = '0' + str(date.month)
        date = str(date.year) + '-' + str(month) + '-01'
        return date

    @api.model
    def _get_to_date(self):
        date = datetime.now()
        m_range = calendar.monthrange(date.year, date.month)
        month = date.month
        if date.month < 10:
            month = '0' + str(date.month)
        date = str(date.year) + '-' + str(month) + '-' + str(m_range[1])
        return date

    @api.model
    def _get_company_id(self):
        return self.env.user.company_id.id
        
    @api.model
    def get_default_employee_id(self):
        user_id = self.env.user.id
        if user_id:
            employee_id = self.env['hr.employee'].search([('user_id','=',user_id)],limit=1)
            if employee_id:
                return employee_id.id
    
    from_date = fields.Date(string='Start Date', default=_get_from_date, required="1")
    to_date = fields.Date(string='End Date', default=_get_to_date, required="1")
    company_id = fields.Many2one('res.company', default=_get_company_id, required="1")
    employee_id = fields.Many2one('hr.employee',string='Employee', required="1")
    state = fields.Selection([('draft','Draft'),('done','Locked')],default='draft',string='State')
    summary_line_ids = fields.One2many('emp.attendance.summary.line','summary_id', string='Summary Lines')
    month_work_days = fields.Integer('Month Days', compute='get_total_work_hour')
    month_total_attandance = fields.Integer('Month Attendances', compute='get_total_work_hour')
    month_work_hour = fields.Integer('Month Hours', compute='get_total_work_hour')
    
    total_work_hour = fields.Float('Total Hour', compute='get_total_work_hour')
    working_hour = fields.Float('Normal Hour', compute='get_total_work_hour')
    overtime_hour = fields.Float('Overtime Hour', compute='get_total_work_hour')
    overtime_salary = fields.Float('Overtime Salary', compute='get_total_work_hour')
    
    normal_ot = fields.Float('Normal OT', compute='get_total_work_hour')
    week_off_ot = fields.Float('Week-Off OT', compute='get_total_work_hour')
    pub_holiday_ot = fields.Float('Pub. Holiday OT', compute='get_total_work_hour')

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Schedule', related="contract_id.resource_calendar_id")
    struct_id = fields.Many2one('hr.payroll.structure', related="contract_id.struct_id", string='Salary Structure')
    

    def generate_summary(self):
        if self.summary_line_ids:
            self.summary_line_ids.unlink()
        
        line_pool = self.env['emp.attendance.summary.line']
        start_date = self.from_date
        end_date = self.to_date
        date = end_date - start_date  

        for i in range(0,date.days+1):
            line_pool.create({
                'date':start_date,
                'summary_id':self.id,
            })
            start_date = start_date+timedelta(days=1)
            
    def action_done(self):
        if not self.summary_line_ids:
            self.generate_summary()
        self.state = 'done'
    
    
    @api.depends('summary_line_ids')
    def get_total_work_hour(self):
        for summary in self:
            
            summary.total_work_hour = 0.0
            summary.overtime_hour = 0.0
            summary.working_hour = 0.0
            summary.month_work_days = 0.0
            summary.month_work_hour = 0.0
            summary.overtime_salary = 0.0
            summary.normal_ot = 0.0
            summary.week_off_ot = 0.0
            summary.pub_holiday_ot = 0.0
            summary.month_total_attandance = 0.0

            month_total_attandance = total_work_hour = working_hour = overtime_hour = month_work_days = overtime_salary = month_work_hour = 0
            normal_ot = week_off_ot = pub_holiday_ot = 0


            for line in summary.summary_line_ids:
                if line.working_hour > 0.0:
                    month_total_attandance += 1 
                if not line.is_holiday and not line.is_public_holiday and line.overtime:
                    normal_ot += line.overtime
                elif line.is_holiday and not line.is_public_holiday and line.overtime:
                    week_off_ot += line.overtime
                elif not line.is_holiday and line.is_public_holiday and line.overtime:
                    pub_holiday_ot += line.overtime
                elif line.is_holiday and line.is_public_holiday and line.overtime:
                    pub_holiday_ot += line.overtime
                    
                if not line.is_holiday:
                    month_work_days += 1
                    month_work_hour += line.work_hour
                total_work_hour += line.working_hour
                overtime_hour += line.overtime
                overtime_salary += line.overtime_salary
            
            summary.total_work_hour = total_work_hour
            summary.overtime_hour = overtime_hour
            summary.working_hour = total_work_hour - overtime_hour
            summary.month_work_days = month_work_days
            summary.month_work_hour = month_work_hour
            summary.overtime_salary = overtime_salary
            summary.normal_ot = normal_ot
            summary.week_off_ot = week_off_ot
            summary.pub_holiday_ot = pub_holiday_ot
            summary.month_total_attandance = month_total_attandance
                    
            
class employee_attendance_summary_line(models.Model):
    _name = 'emp.attendance.summary.line'
    
    
    date = fields.Date('Date')
    day = fields.Char('Day', compute='_get_day')
    in_time = fields.Float('In Time', compute='_get_in_out_time')
    out_time = fields.Float('Out Time', compute='_get_in_out_time')
    summary_id = fields.Many2one('emp.attendance.summary','Summary')
    is_holiday = fields.Boolean('Week-Off',compute='_is_holiday')
    work_hour = fields.Float('Working Hour', compute='_is_holiday')
    break_hour = fields.Float('Break Hour', compute='_get_in_out_time')
    working_hour = fields.Float('Worked Hour', compute='_get_in_out_time')
    overtime = fields.Float('Overtime', compute='_get_working_hour')
    resource_id = fields.Many2one('resource.calendar', string='Working Hour', compute='_is_holiday')
    is_public_holiday = fields.Boolean('Holidays', compute='_is_holiday')
    overtime_salary = fields.Float('Overtime Salary', compute='_is_holiday')
    is_rest_day = fields.Boolean('Rest Days')
    
    
    @api.depends('in_time','out_time')
    def _get_working_hour(self):
        for line in self:
            line.overtime = 0.0
            line._is_holiday()
            overtime_schedule = line.summary_id.company_id.overtime_schedule
            if line.in_time and line.out_time:
                worked_hour = line.working_hour
                if line.is_holiday or line.is_public_holiday:
                    line.overtime = worked_hour
                else:
                    # line.working_hour = worked_hour
                    line.working_hour = abs(abs(line.in_time - line.out_time) - line.break_hour)
                    # line.working_hour = worked_hour
                    # line.working_hour = worked_hour
                    overtime = worked_hour - line.work_hour
                    if overtime > 0:
                        if overtime > overtime_schedule:
                            line.overtime = overtime
            
    
    @api.depends('date')
    def _get_day(self):
        for line in self:
            if line.date:
                date = line.date
                line.day = calendar.day_name[date.weekday()]
            else:
                line.day = None
    
    def get_float_time(self,date):
        date = fields.Datetime.from_string(date)
        date = to_naive_user_tz(date, self.env.user)
        time = float(str(date.hour)+'.'+str(date.minute))
        return time
    
    @api.depends('date')
    def _get_in_out_time(self):
        attendance_pool= self.env['hr.attendance']
        for line in self:
            total_hours = 0.0
            line.in_time = 0.0
            line.out_time = 0.0
            line.break_hour = 0.0
            line.working_hour = 0.0
            if line.date:
                line_date  = line.date.strftime("%Y-%m-%d")
                s_date = line_date+' 00:00:00'
                e_date = line_date+' 23:59:59'
                attendance_ids = attendance_pool.search([('check_in','>=',s_date),('check_out','<=',e_date),('employee_id','=',line.summary_id.employee_id.id)],order='check_in asc')
                line.is_rest_day = False
                if line.summary_id.contract_id and line.summary_id.contract_id.work_type == 'part_time':
                    for att in attendance_ids:
                        if att.rest_day:
                            line.is_rest_day = True
                if attendance_ids:
                    if len(attendance_ids) == 1:
                        first = attendance_pool.browse(attendance_ids.ids[0])
                        last = attendance_pool.browse(attendance_ids.ids[0])
                        line.in_time = self.get_float_time(attendance_ids.check_in)
                        line.out_time = self.get_float_time(attendance_ids.check_out)

                        start_time = datetime.strptime(str(first.check_in.time()), "%H:%M:%S")
                        end_time = datetime.strptime(str(last.check_out.time()), "%H:%M:%S")

                        # get difference
                        delta = end_time - start_time

                        sec = delta.total_seconds()
                        min = sec / 60
                        total_hours = sec / (60 * 60)
                        day = self.get_dayofweek_number(line.day)
                        resource_id = self.get_resource_calander(line)
                        if resource_id:
                            for res in resource_id.attendance_ids:
                                if day == int(res.dayofweek):
                                    line.out_time += res.break_hour
                    else:
                        first = attendance_pool.browse(attendance_ids.ids[0])
                        last = attendance_pool.browse(attendance_ids.ids[-1])
                        line.in_time = self.get_float_time(first.check_in)
                        line.out_time = self.get_float_time(last.check_out)

                        start_time = datetime.strptime(str(first.check_in.time()), "%H:%M:%S")
                        end_time = datetime.strptime(str(last.check_out.time()), "%H:%M:%S")

                        # get difference
                        delta = end_time - start_time

                        sec = delta.total_seconds()
                        min = sec / 60
                        total_hours = sec / (60 * 60)

                # set break hours  and overtime and worked hours
                if len(attendance_ids) > 1:
                    attendance_len = len(attendance_ids)
                    hours = sum(attendance_ids.mapped('worked_hours'))
                    line.break_hour = total_hours - hours
                    line.working_hour  = abs(total_hours - line.break_hour)
                else:
                    day = self.get_dayofweek_number(line.day)
                    resource_id = self.get_resource_calander(line)
                    if resource_id:
                        for res in resource_id.attendance_ids:
                            if day == int(res.dayofweek):
                                line.break_hour = res.break_hour
                    line.working_hour  = abs(total_hours)
     
    def get_resource_calander(self,line):
        date = line.date
        company_id = line.summary_id.company_id and line.summary_id.company_id.id or False
        employee_id = line.summary_id.employee_id.id
        if line.summary_id.employee_id and line.summary_id.employee_id.resource_calendar_id:
            resouce_id = line.summary_id.employee_id.resource_calendar_id
            if resouce_id:
                return resouce_id
        return False
    
    def get_dayofweek_number(self,day):
        if day == 'Monday':
            return 0
        elif day == 'Tuesday':
            return 1
        elif day == 'Wednesday':
            return 2
        elif day == 'Thursday':
            return 3
        elif day == 'Friday':
            return 4
        elif day == 'Saturday':
            return 5
        elif day == 'Sunday':
            return 6
    
    @api.depends('day')
    def _is_holiday(self):
        for line in self:
            if line.summary_id.contract_id and line.summary_id.contract_id.work_type == 'full_time':
                if line.day:
                    line.is_holiday = False
                    line.is_public_holiday = False
                    line.overtime_salary = 0.0
                    line.work_hour = 0.0
                    day = self.get_dayofweek_number(line.day)
                    working_days = []
                    resource_id = self.get_resource_calander(line)
                    if resource_id:
                        line.resource_id = resource_id.id
                        for res in resource_id.attendance_ids:
                            if day == int(res.dayofweek):
                                line.work_hour = abs(abs(res.hour_from - res.hour_to) - res.break_hour)
                            working_days.append(int(res.dayofweek))
                        
                    if working_days:
                        if day not in working_days:
                            line.is_holiday = True
                    
                    if line.resource_id and line.date:
                        domain = [('calendar_id','=',line.resource_id.id),('date_from','<=',line.date),('date_to','>=',line.date), ('resource_id', '=', False)]
                        leave_id = self.env['resource.calendar.leaves'].search(domain)
                        if leave_id:
                            if not leave_id.holiday_id:
                                line.is_public_holiday  = True
                    
                    if line.resource_id and line.summary_id.contract_id and line.overtime > 0.0:
                        wage = 0
                        if line.summary_id and line.summary_id.contract_id:
                            wage_by_hours = line.summary_id.contract_id.wage_by_hours
                        
                        rate = line.resource_id.normal_day_overtime
                        if line.is_holiday:
                            rate = line.resource_id.off_day_overtime
                        if line.is_public_holiday:
                            rate = line.resource_id.holiday_overtime
                        
                        if rate:
                            wage_by_hours = wage_by_hours * rate

                        if line.summary_id and line.summary_id.contract_id:
                            if line.summary_id.contract_id.wage_by == 'by_hours':
                                line.overtime_salary = line.overtime * wage_by_hours
                            else:
                                wage = line.summary_id.contract_id.wage
                                line.overtime_salary = line.overtime * wage
                        
            else:
                line.is_holiday = False
                line.is_public_holiday = False
                line.overtime_salary = 0.0
                line.work_hour = abs(line.out_time - line.in_time)
                rate = line.resource_id.normal_day_overtime
                if line.is_rest_day:
                    line.is_holiday = True
                    line.overtime = line.work_hour
                    rate = line.summary_id.employee_id.resource_calendar_id.off_day_overtime
                
                wage = 0
                if line.summary_id and line.summary_id.contract_id:
                    wage = line.summary_id.contract_id.wage_by_hours
                if not wage and line.summary_id.summary_line_ids:
                    wage = line.summary_id.contract_id.wage
                    wage = wage / len(line.summary_id.summary_line_ids)
                wage = wage * rate
                line.overtime_salary = line.overtime * wage
