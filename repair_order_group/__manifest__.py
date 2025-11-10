# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Order Group",
    "summary": "Group several repair orders and keep them in sync",
    "version": "18.0.1.0.0",
    "category": "Repair",
    "license": "AGPL-3",
    "author": "Cetmix OÜ, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": ["repair"],
    "data": [
        "data/repair_order_group_data.xml",
        "security/ir.model.access.csv",
        "views/repair_order_group_views.xml",
        "views/repair_order_views.xml",
    ],
    "demo": [
        "demo/repair_order_group_demo.xml",
    ],
    "installable": True,
    "application": False,
}
