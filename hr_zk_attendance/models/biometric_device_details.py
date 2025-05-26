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
import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True,
                          help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True,
                               help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address',
                               help='Working address of the partner')
    company_id = fields.Many2one('res.company', string='Company',
                               default=lambda self: self.env.company.id,
                               help='Current Company')
    active = fields.Boolean(default=True)

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception as e:
            _logger.error("Connection error: %s", str(e))
            return False

    def action_test_connection(self):
        """Checking the connection status"""
        self.ensure_one()
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=False, ommit_ping=False)
        try:
            conn = self.device_connect(zk)
            if conn:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Successfully Connected'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise ValidationError(_("Could not connect to the device. Please check the device configuration."))
        except Exception as error:
            raise ValidationError(_(
                "Connection failed: %s", str(error)))

    def action_set_timezone(self):
        """Function to set user's timezone to device"""
        self.ensure_one()
        machine_ip = self.device_ip
        zk_port = self.port_number
        try:
            zk = ZK(machine_ip, port=zk_port, timeout=15,
                    password=0, force_udp=False, ommit_ping=False)
        except NameError:
            raise UserError(
                _("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
        
        conn = self.device_connect(zk)
        if conn:
            try:
                user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
                user_timezone = pytz.timezone(user_tz)
                user_timezone_time = pytz.utc.localize(fields.Datetime.now()).astimezone(user_timezone)
                conn.set_time(user_timezone_time)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Successfully Set the Time'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                raise UserError(_("Failed to set timezone: %s", str(e)))
            finally:
                conn.disconnect()
        else:
            raise UserError(_("Please Check the Connection"))

    def action_clear_attendance(self):
        """Method to clear record from the zk.machine.attendance model and from the device"""
        self.ensure_one()
        try:
            zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                    password=0, force_udp=False, ommit_ping=False)
        except NameError:
            raise UserError(_("Please install pyzk with 'pip3 install pyzk'."))
        
        conn = self.device_connect(zk)
        if not conn:
            raise UserError(_('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
        
        try:
            conn.enable_device()
            clear_data = conn.get_attendance()
            if clear_data:
                conn.clear_attendance()
                self.env.cr.execute("DELETE FROM zk_machine_attendance")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Successfully cleared attendance data'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('No attendance records found to clear.'))
        except Exception as error:
            raise ValidationError(str(error))
        finally:
            conn.disconnect()

    @api.model
    def cron_download(self):
        """Cron job to download attendance from all devices"""
        devices = self.search([('active', '=', True)])
        for device in devices:
            try:
                device.action_download_attendance()
            except Exception as e:
                _logger.error("Error downloading attendance from device %s: %s", device.name, str(e))

    def action_download_attendance(self):
        """Function to download attendance records from the device"""
        self.ensure_one()
        _logger.info("Starting attendance download from device: %s", self.name)
        
        try:
            zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                    password=0, force_udp=False, ommit_ping=False)
        except NameError:
            raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
        
        conn = self.device_connect(zk)
        if not conn:
            raise UserError(_("Unable to connect to the device."))
        
        try:
            conn.disable_device()
            users = conn.get_users()
            attendance = conn.get_attendance()
            
            if not attendance:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('No new attendance records found'),
                        'type': 'info',
                        'sticky': False,
                    }
                }
            
            user_dict = {user.user_id: user for user in users}
            ZkAttendance = self.env['zk.machine.attendance'].sudo()
            
            attendance_vals = []
            for record in attendance:
                user_id = record.user_id
                if user_id not in user_dict:
                    continue
                
                # Convert to UTC
                local_tz = pytz.timezone(self.env.user.tz or 'UTC')
                local_dt = local_tz.localize(record.timestamp, is_dst=None)
                utc_dt = local_dt.astimezone(pytz.utc)
                atten_time = fields.Datetime.to_string(utc_dt)
                
                employee = self.env['hr.employee'].sudo().search([
                    ('device_id_num', '=', user_id)
                ], limit=1)
                
                if not employee:
                    employee = self.env['hr.employee'].sudo().create({
                        'name': user_dict[user_id].name,
                        'device_id_num': user_id,
                    })
                
                # Check for duplicate
                if not ZkAttendance.search_count([
                    ('device_id_num', '=', user_id),
                    ('punching_time', '=', atten_time)
                ]):
                    attendance_vals.append({
                        'employee_id': employee.id,
                        'device_id_num': user_id,
                        'punching_time': atten_time,
                        'attendance_type': str(record.status),
                        'punch_type': str(getattr(record, 'punch', '0')),
                        'address_id': self.address_id.id,
                        'company_id': employee.company_id.id or self.env.company.id,
                    })
            
            if attendance_vals:
                ZkAttendance.create(attendance_vals)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Successfully downloaded %s attendance records', len(attendance_vals)),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('No new attendance records to import'),
                        'type': 'info',
                        'sticky': False,
                    }
                }
        
        except Exception as e:
            raise UserError(_("Error downloading attendance: %s", str(e)))
        finally:
            try:
                conn.enable_device()
                conn.disconnect()
            except Exception:
                pass

    def action_restart_device(self):
        """Function to restart the device"""
        self.ensure_one()
        try:
            zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                    password=0, force_udp=False, ommit_ping=False)
        except NameError:
            raise UserError(_("Please install pyzk with 'pip3 install pyzk'."))
        
        conn = self.device_connect(zk)
        if not conn:
            raise UserError(_('Unable to connect to the device.'))
        
        try:
            conn.restart()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _('Device restart initiated successfully'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as error:
            raise ValidationError(str(error))
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass
