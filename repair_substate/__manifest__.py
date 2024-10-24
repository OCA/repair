# Copyright 2024 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Repair Sub State",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "author": "360ERP, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "license": "AGPL-3",
    "depends": ["base_substate", "repair"],
    "data": [
        "views/repair_views.xml",
        "data/repair_substate_data.xml",
    ],
    "installable": True,
}
