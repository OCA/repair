# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Stock Consumption Step",
    "summary": """Adds a warehouse-configurable step to process repair consumption
    moves in a picking""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "maintainers": ["sbejaoui"],
    "depends": ["repair", "repair_warehouse"],
    "excludes": ["repair_stock_move"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/repair_consumption_partial_wizard.xml",
        "views/repair_order.xml",
        "views/stock_warehouse.xml",
    ],
    "demo": [],
}
