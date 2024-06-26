from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import calendar
from datetime import datetime

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    extended_workdays = fields.Boolean(string="Regular Work Day")
    fix_month_salary = fields.Boolean(string="Fix Work Days")

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    sum_worked_hours = fields.Float(compute='_compute_worked_hours', store=True, help='Total hours of attendance and time off (paid or not)')

    @api.depends('worked_days_line_ids.number_of_hours')
    def _compute_worked_hours(self):
        for payslip in self:
            payslip.sum_worked_hours = sum([line.number_of_hours for line in payslip.worked_days_line_ids])

    # Total Public Holiday In Month
    def get_public_holidays_dates(self):
        public_holidays = []
        total_holiday_date = []
        min_time = datetime.min.time()
        max_time = datetime.max.time()
        date_from = datetime.combine(self.date_from, min_time)
        date_too = datetime.combine(self.date_to, max_time)
        leaves_ids = self.env['resource.calendar.leaves'].search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to), ('resource_id', '=',False)])
        for leave in leaves_ids:
            curr_date = leave.date_from.date()
            end_date = leave.date_to.date()
            while curr_date <= end_date:
                public_holidays.append(curr_date.strftime("%Y-%m-%d"))
                curr_date += timedelta(days=1)
        total_holidays = len(public_holidays)
        return total_holidays

    #Total unpaid sick and paid leave emoloyee
    def _total_leaves(self, employee):
        leave_ids = self.env['hr.leave'].search([
            ('state', '=', 'validate'),('employee_id', '=', employee.id),
            ('request_date_from', '>=', self.date_from),('request_date_to', '<=', self.date_to)])
        total_leave = sum(leave_ids.mapped('number_of_days'))
        return total_leave

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        res = self.get_worked_day_lines(self.contract_id, self.date_from, self.date_to)
        self.ensure_one()
        contract = self.contract_id
        if self.struct_id.extended_workdays or self.struct_id.fix_month_salary:
            self.worked_days_line_ids = [(5,0,0)]
            res = []
            if self.struct_id.extended_workdays:
                # Work Hour
                work_entry_type = self.env.ref('pways_payslip_attendance_sheet.work_entry_type_work_hour')
                rr = {
                       'sequence': work_entry_type.sequence,
                       'name': _("NORMAL WORK HOURS"),
                       'code': work_entry_type.code,
                       'number_of_hours': float(self.summary_id and self.summary_id.working_hour or 0.0),
                       'number_of_days':float(self.summary_id and self.summary_id.month_work_days or 0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
                total_holidays = self.get_public_holidays_dates()
                holiday_hours = self.contract_id.resource_calendar_id.hours_per_day * total_holidays
                # LEAVE
                work_entry_type = self.env.ref('pways_attend_sheet_based_payslip.work_entry_type_overtime_leave')
                rr = {
                       'sequence': work_entry_type.sequence,
                        'name': _("TOTAL LEAVE"),
                        'code': work_entry_type.code,
                       'number_of_hours': float(0.0),
                       'number_of_days':float(0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
                # Normal Overtime
                work_entry_type = self.env.ref('pways_payslip_attendance_sheet.work_entry_type_overtime_hours')
                rr = {
                       'sequence': work_entry_type.sequence,
                       'name': _("OVERTIME HOURS"),
                       'code': work_entry_type.code,
                       'number_of_hours': float(self.summary_id and self.summary_id.normal_ot or 0.0),
                       'number_of_days':float(0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
                # Weekoff OT
                work_entry_type = self.env.ref('pways_attend_sheet_based_payslip.work_entry_type_overtime_weekoff_hours')
                rr = {
                       'sequence': work_entry_type.sequence,
                        'name': _("OVERTIME WEEKOFF"),
                        'code': work_entry_type.code,
                       'number_of_hours': float(self.summary_id and self.summary_id.week_off_ot or 0.0),
                       'number_of_days':float(self.summary_id and self.summary_id.month_work_days or 0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
                # Public holiday
                work_entry_type = self.env.ref('pways_attend_sheet_based_payslip.work_entry_type_overtime_holiday_hours')
                rr = {
                       'sequence': work_entry_type.sequence,
                       'name': _("OVERTIME PUBLIC HOLIDAY"),
                       'code': work_entry_type.code,
                       'number_of_hours': float(self.summary_id and self.summary_id.pub_holiday_ot or 0.0),
                       'number_of_days':float(0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
                worked_days_lines = self.worked_days_line_ids.browse([])
                for r in res:
                    worked_days_lines += worked_days_lines.new(r)
                self.worked_days_line_ids = worked_days_lines
                # TOTAL_PUB_HOLIDAY
                work_entry_type = self.env.ref('pways_attend_sheet_based_payslip.work_entry_type_overtime_holiday_day')
                rr = {
                       'sequence': work_entry_type.sequence,
                        'name': _("TOTAL PUBLIC HOLIDAYS"),
                        'code': work_entry_type.code,
                       'number_of_hours': float(0.0),
                       'number_of_days':float(0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
                total_leave = self._total_leaves(self.employee_id)
                leave_hours = self.contract_id.resource_calendar_id.hours_per_day * total_leave
            else:
                work_entry_type = self.env.ref('pways_payslip_attendance_sheet.work_entry_type_work_hour')
                rr = {
                       'sequence': work_entry_type.sequence,
                       'name': _("FIX MONTHLY SALARY"),
                       'code': work_entry_type.code,
                       'number_of_hours': float(self.summary_id and self.summary_id.working_hour or 0.0),
                       'number_of_days':float(self.summary_id and self.summary_id.month_total_attandance or 0.0),
                       'contract_id' : contract and contract.id or False}
                res.append(rr)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in res:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

    def create_work_days_lines(self):
        if self.summary_id:
            for line in self.worked_days_line_ids:
                # Public Holiday
                if line.code == 'OVERTIME_PUB_HOLIDAY':
                    line.number_of_hours = float(self.summary_id and self.summary_id.pub_holiday_ot or 0.0)
                    line.number_of_days = 0.0
                # Overtime Weekoff
                elif line.code == 'OVER_TIME_WEEKOFF':
                    line.number_of_hours = float(self.summary_id and self.summary_id.week_off_ot or 0.0)
                    line.number_of_days = 0.0
                # Normal Overtime 
                elif line.code == 'OVER_TIME':
                    line.number_of_hours = float(self.summary_id and self.summary_id.normal_ot or 0.0)
                    line.number_of_days = 0.0
                # LEAVE
                elif line.code == 'LEAVE':
                    total_leave = self._total_leaves(self.employee_id)
                    leave_hours = self.contract_id.resource_calendar_id.hours_per_day * total_leave
                    line.number_of_hours = leave_hours
                    line.number_of_days = total_leave
                # TOTAL_PUB_HOLIDAY
                elif line.code == 'TOTAL_PUB_HOLIDAY':
                    total_holidays = self.get_public_holidays_dates()
                    holiday_hours = self.contract_id.resource_calendar_id.hours_per_day * total_holidays
                    line.number_of_hours = holiday_hours
                    line.number_of_days = total_holidays


    @api.onchange('struct_id','date_from', 'date_to')
    def onchange_struct_id(self):
        res = super(HRPayslip, self).onchange_struct_id()
        if self.struct_id:
        #     if not self.summary_id:
        #         self.create_attendance_summary(self)
            self._get_worked_day_lines()
            self.create_work_days_lines()
            return res

    def compute_sheet(self):
        # self.create_attendance_summary(self)
        self._get_worked_day_lines()
        self.create_work_days_lines()
        super(HRPayslip, self).compute_sheet()
        return True

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    amount = fields.Float(compute='_compute_amount')

    @api.depends('payslip_id','number_of_days','number_of_hours')
    def _compute_amount(self):
        normal_wage = 0
        if self.contract_id:
            if self.contract_id.wage:
                normal_wage = self.contract_id.wage
            if self.contract_id.wage_by_hours:
                normal_wage = self.contract_id.wage_by_hours

        for worked_days in self:
            worked_days.amount = 0.0
            wage_by_hours = worked_days.payslip_id.contract_id.wage_by_hours
            if worked_days.payslip_id.struct_id.fix_month_salary:
                days = worked_days.payslip_id.summary_id.month_work_days
                month_attandance = worked_days.payslip_id.summary_id.month_total_attandance
                if worked_days.code == "WORK_HOUR" and days > 0:
                    amount = worked_days.payslip_id.contract_id.wage / days
                    worked_days.amount = amount * month_attandance
            elif worked_days.code == "WORK_HOUR":
                # if worked_days.payslip_id.wage_type == "hourly":
                if worked_days.payslip_id.contract_id.wage_by == "by_hours":
                    worked_days.amount =  wage_by_hours * worked_days.number_of_hours or 0
                else:
                    worked_days.amount = normal_wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) or 0
            elif worked_days.code == "OVERTIME_PUB_HOLIDAY":
                if worked_days.payslip_id.contract_id.wage_by == "by_hours":
                    worked_days.amount =  (wage_by_hours * worked_days.payslip_id.contract_id.resource_calendar_id.holiday_overtime) * worked_days.number_of_hours or 0
                else:
                    holiday_overtime = worked_days.payslip_id.contract_id.resource_calendar_id.holiday_overtime * worked_days.payslip_id.contract_id.wage
                    holiday_overtime_total = holiday_overtime/100 if holiday_overtime > 0 else 0
                    worked_days.amount = holiday_overtime_total * worked_days.number_of_hours
            elif worked_days.code == "OVER_TIME_WEEKOFF":
                if worked_days.payslip_id.contract_id.wage_by == "by_hours":
                    worked_days.amount =  (wage_by_hours * worked_days.payslip_id.contract_id.resource_calendar_id.off_day_overtime) * worked_days.number_of_hours or 0
                else:
                    weekoff_amount = worked_days.payslip_id.contract_id.resource_calendar_id.off_day_overtime * worked_days.payslip_id.contract_id.wage
                    weekoff_amount_total = weekoff_amount/100 if weekoff_amount > 0 else 0
                    worked_days.amount = weekoff_amount_total * worked_days.number_of_hours
            elif worked_days.code == "OVER_TIME":
                if worked_days.payslip_id.contract_id.wage_by == "by_hours":
                    worked_days.amount =  (wage_by_hours * worked_days.payslip_id.contract_id.resource_calendar_id.normal_day_overtime) * worked_days.number_of_hours or 0
                else:
                    overtime_amount = worked_days.payslip_id.contract_id.resource_calendar_id.normal_day_overtime * worked_days.payslip_id.contract_id.wage
                    overtime_amount_total = overtime_amount/100 if overtime_amount > 0 else 0
                    worked_days.amount = overtime_amount_total * worked_days.number_of_hours
            # elif worked_days.code == "HOLIDAY_OVERTIME":
            #     if worked_days.payslip_id.contract_id.wage_by == "by_hours":
            #         worked_days.amount = worked_days.amount = worked_days.payslip_id.contract_id.wage_by_hours * worked_days.number_of_hours
            #     else:
            #         worked_days.amount = normal_wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) or 0
            elif worked_days.code == "TOTAL_PUB_HOLIDAY":
                if worked_days.payslip_id.contract_id.wage_by == "by_hours":
                    worked_days.amount = worked_days.payslip_id.contract_id.wage_by_hours * worked_days.number_of_hours
                else:
                    worked_days.amount = normal_wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) or 0
            