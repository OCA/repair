# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Repair Security",
    "summary": "Create security groups for Repair",
    "version": "16.0.1.0.0",
    "category": "Manufacturing",
    "website": "https://github.com/OCA/repair",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["repair"],
    "data": [
        "security/repair_security.xml",
        "security/ir.model.access.csv",
        "views/repair_views.xml",
    ],
    "post_init_hook": "post_init_hook",
}
