# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Sent",
    "summary": """Adds the "Quotation Sent" status to repair orders""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": ["repair"],
    "data": [
        "views/repair_order.xml",
    ],
    "demo": [],
}
