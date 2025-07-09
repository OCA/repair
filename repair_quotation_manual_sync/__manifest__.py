# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair Quotation Manual Sync",
    "summary": """
        Manually Synchronize Repair Orders with their Quotations
    """,
    "version": "17.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["repair"],
    "data": [
        "views/repair_order_views.xml",
        "views/sale_order_views.xml",
    ],
}
