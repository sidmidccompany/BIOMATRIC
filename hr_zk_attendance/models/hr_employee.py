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
from odoo import fields, models


class HrEmployee(models.Model):
    """Inherit the model to add biometric device fields"""
    _inherit = 'hr.employee'

    device_id_num = fields.Char(
        string='Biometric Device ID',
        help="Give the biometric device id",
        copy=False,
        index=True
    )

    _sql_constraints = [
        ('unique_device_id',
         'UNIQUE(device_id_num)',
         'The Biometric Device ID must be unique!')
    ]
