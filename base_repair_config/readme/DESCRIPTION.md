This module provides an empty general settings section for the repair
configuration.

This is a technical module and it doesn't provide any new functionality.
Extend this module to add general settings related to the repair app.

When extending the general settings view, here is an example of how the
code would look like:

``` xml
<record id="res_config_settings_view_form_inherit" model="ir.ui.view">
    <field name="name">res.config.settings.view.form.inherit.repair</field>
    <field name="model">res.config.settings</field>
    <field name="inherit_id" ref="base_repair_config.res_config_settings_view_form"/>
    <field name="arch" type="xml">
        <xpath expr="//block[@name='repair_setting_container']" position="inside">
            <setting id="extra_repair_setting" help="Enable extra repair configuration options.">
                <field name="extra_repair_field"/>
            </setting>
            <setting id="another_repair_setting" help="Another repair-related setting.">
                <field name="another_repair_field"/>
            </setting>
        </xpath>
    </field>
</record>
```
