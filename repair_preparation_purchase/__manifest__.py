# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Preparation Purchase",
    "summary": """This addon add link""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": ["repair_preparation", "purchase_stock"],
    "data": [
        "views/purchase_order.xml",
        "views/repair_order.xml",
    ],
    "demo": [],
}
