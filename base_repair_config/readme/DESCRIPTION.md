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
           <xpath expr="//div[@name='repair_setting_container']" position="inside">
                <div class="col-lg-6 o_setting_box" id="extra_repair_setting">
                    <div class="o_setting_left_pane">
                        <field name="extra_repair_setting" />
                    </div>
                    <div class="o_setting_right_pane">
                        <label for="extra_repair_setting" />
                        <div class="text-muted">Enable extra repair configuration options.</div>
                    </div>
                </div>
                <div class="col-lg-6 o_setting_box" id="another_repair_setting">
                    <div class="o_setting_left_pane">
                        <field name="another_repair_setting" />
                    </div>
                    <div class="o_setting_right_pane">
                        <label for="another_repair_setting" />
                        <div class="text-muted">Another repair-related setting.</div>
                    </div>
                </div>
           </xpath>
       </field>
   </record>
```
