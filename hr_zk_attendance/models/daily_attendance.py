# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models, tools


class DailyAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'daily.attendance'
    _description = 'Daily Attendance Report'
    _auto = False
    _order = 'punching_day desc'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                help='Employee Name', readonly=True)
    punching_day = fields.Datetime(string='Date', help='Date of punching',
                                readonly=True)
    address_id = fields.Many2one('res.partner', string='Working Address',
                              help='Working address of the employee',
                              readonly=True)
    attendance_type = fields.Selection([
        ('1', 'Finger'),
        ('15', 'Face'),
        ('2', 'Type_2'),
        ('3', 'Password'),
        ('4', 'Card')
    ], string='Category', help='Attendance detecting methods', readonly=True)
    punch_type = fields.Selection([
        ('0', 'Check In'),
        ('1', 'Check Out'),
        ('2', 'Break Out'),
        ('3', 'Break In'),
        ('4', 'Overtime In'),
        ('5', 'Overtime Out')
    ], string='Punching Type', help='The Punching Type of attendance',
        readonly=True)
    punching_time = fields.Datetime(string='Punching Time',
                                help='Punching time in the device',
                                readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def init(self):
        """Initialize the SQL view for attendance report"""
        tools.drop_view_if_exists(self.env.cr, 'daily_attendance')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW daily_attendance AS (
                WITH latest_attendance AS (
                    SELECT 
                        id,
                        employee_id,
                        punching_time,
                        write_date,
                        address_id,
                        attendance_type,
                        punch_type,
                        company_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY employee_id, DATE(punching_time)
                            ORDER BY punching_time DESC
                        ) as rn
                    FROM zk_machine_attendance
                    WHERE employee_id IS NOT NULL
                )
                SELECT
                    la.id as id,
                    la.employee_id,
                    la.punching_time as punching_day,
                    la.address_id,
                    la.attendance_type,
                    la.punching_time,
                    la.punch_type,
                    la.company_id,
                    e.name as employee_name
                FROM latest_attendance la
                JOIN hr_employee e ON la.employee_id = e.id
                WHERE la.rn = 1
                ORDER BY la.punching_time DESC
            )
        """)
