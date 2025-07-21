# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair Sale Multi",
    "version": "18.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "summary": "Repair Sale Multi",
    "category": "Repair",
    "depends": ["repair"],
    "data": [
        "security/ir.model.access.csv",
        "views/repair_order_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "license": "AGPL-3",
    "maintainers": ["AaronHForgeFlow"],
}
