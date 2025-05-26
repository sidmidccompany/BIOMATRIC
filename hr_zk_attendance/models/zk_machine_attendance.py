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
from odoo import api, fields, models


class ZkMachineAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'zk.machine.attendance'
    _description = 'Biometric Device Attendance'
    _order = 'punching_time DESC'

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee',
        required=True,
        index=True,
        ondelete='cascade'
    )
    check_in = fields.Datetime(
        string='Check In',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    check_out = fields.Datetime(
        string='Check Out',
        index=True
    )
    device_id_num = fields.Char(
        string='Biometric Device ID',
        help="The ID of the Biometric Device",
        index=True,
        required=True
    )
    punch_type = fields.Selection([
        ('0', 'Check In'),
        ('1', 'Check Out'),
        ('2', 'Break Out'),
        ('3', 'Break In'),
        ('4', 'Overtime In'),
        ('5', 'Overtime Out'),
        ('255', 'Duplicate')
    ], string='Punching Type',
        help='Punching type of the attendance',
        default='0',
        required=True
    )
    attendance_type = fields.Selection([
        ('1', 'Finger'),
        ('15', 'Face'),
        ('2', 'Type_2'),
        ('3', 'Password'),
        ('4', 'Card'),
        ('255', 'Duplicate')
    ], string='Category',
        help="Attendance detecting methods",
        default='1',
        required=True
    )
    punching_time = fields.Datetime(
        string='Punching Time',
        help="Punching time in the device",
        index=True,
        required=True
    )
    address_id = fields.Many2one(
        'res.partner',
        string='Working Address',
        help="Working address of the employee",
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='employee_id.company_id',
        store=True,
        index=True
    )

    _sql_constraints = [
        ('unique_device_punch',
         'UNIQUE(device_id_num, punching_time)',
         'Duplicate attendance record detected!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to properly handle check-in/check-out"""
        for vals in vals_list:
            if vals.get('punch_type') == '0':  # Check In
                vals['check_in'] = vals.get('punching_time')
            elif vals.get('punch_type') == '1':  # Check Out
                vals['check_out'] = vals.get('punching_time')
        return super().create(vals_list)
