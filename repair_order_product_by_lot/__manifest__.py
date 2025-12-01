# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Order Product by Lot",
    "summary": "Select product in repair order by the lot number",
    "version": "18.0.1.0.0",
    "category": "Repair",
    "license": "AGPL-3",
    "author": "Cetmix OÜ, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": [
        "repair",
    ],
    "data": [
        "views/repair_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
