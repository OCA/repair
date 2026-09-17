# Copyright 2026 Escodoo - Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Timesheet Default Project",
    "summary": "Configure a default Project and Task for Repair Order timesheets",
    "version": "18.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_repair_config",
        "repair_timesheet",
    ],
    "maintainers": ["CristianoMafraJunior"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/repair_order_views.xml",
    ],
}
