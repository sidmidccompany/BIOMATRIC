<?xml version="1.0" encoding="UTF-8" ?>
<odoo>
    <!-- Daily Attendance tree view -->
    <record id="view_daily_attendance_tree" model="ir.ui.view">
        <field name="name">daily.attendance.tree</field>
        <field name="model">daily.attendance</field>
        <field name="arch" type="xml">
            <tree string="Daily Attendance" create="false" edit="false" delete="false">
                <field name="employee_id"/>
                <field name="punching_day"/>
                <field name="punching_time"/>
                <field name="punch_type"/>
                <field name="attendance_type"/>
                <field name="address_id"/>
                <field name="company_id" groups="base.group_multi_company"/>
            </tree>
        </field>
    </record>

    <!-- Daily Attendance search view -->
    <record id="view_daily_attendance_search" model="ir.ui.view">
        <field name="name">daily.attendance.search</field>
        <field name="model">daily.attendance</field>
        <field name="arch" type="xml">
            <search string="Daily Attendance">
                <field name="employee_id"/>
                <field name="punching_day"/>
                <field name="address_id"/>
                <filter string="Today" name="today" domain="[('punching_day', '&gt;=', datetime.datetime.combine(context_today(), datetime.time(0,0,0))), ('punching_day', '&lt;=', datetime.datetime.combine(context_today(), datetime.time(23,59,59)))]"/>
                <filter string="Current Month" name="current_month" domain="[('punching_day', '&gt;=', (context_today() + relativedelta(day=1)).strftime('%Y-%m-%d')), ('punching_day', '&lt;=', (context_today() + relativedelta(months=1, day=1, days=-1)).strftime('%Y-%m-%d'))]"/>
                <group expand="0" string="Group By">
                    <filter string="Employee" name="employee" context="{'group_by': 'employee_id'}"/>
                    <filter string="Date" name="date" context="{'group_by': 'punching_day:day'}"/>
                    <filter string="Type" name="type" context="{'group_by': 'punch_type'}"/>
                    <filter string="Location" name="location" context="{'group_by': 'address_id'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- Daily Attendance action -->
    <record id="action_daily_attendance_report" model="ir.actions.act_window">
        <field name="name">Daily Attendance Report</field>
        <field name="res_model">daily.attendance</field>
        <field name="view_mode">tree</field>
        <field name="search_view_id" ref="view_daily_attendance_search"/>
        <field name="context">{'search_default_today': 1}</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                No attendance records found
            </p>
            <p>
                This report shows the daily attendance records from your biometric devices.
            </p>
        </field>
    </record>
</odoo>
