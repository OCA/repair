# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair To Sale Order",
    "version": "15.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "summary": "Repair To Sale Order",
    "category": "Repair",
    "depends": ["repair_type", "sale"],
    "data": [
        "views/repair_order_view.xml",
        "views/sale_order_view.xml",
        "views/repair_type_view.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "license": "AGPL-3",
    "maintainers": ["ChrisOForgeFlow"],
    "application": False,
}
