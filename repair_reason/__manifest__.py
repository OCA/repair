# Copyright 2023 ForgeFlow S. L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Repair Reason",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "Repair",
    "summary": """Repair Reason""",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": [
        "repair",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/repair_reason_view.xml",
        "views/repair_order_view.xml",
    ],
    "installable": True,
}
