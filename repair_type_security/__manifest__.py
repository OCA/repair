# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Repair Types Security",
    "summary": "Glue module Repair Type and Repair Security",
    "version": "15.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["repair_type", "repair_security"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "post_init_hook": "post_init_hook",
    "development_status": "Alpha",
    "auto_install": True,
}
