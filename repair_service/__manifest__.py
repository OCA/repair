# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair Service",
    "summary": """
        Adds services to repair orders, so that they can be added
        as sale order lines.
    """,
    "version": "18.0.1.1.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["repair"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/repair_views.xml",
    ],
}
