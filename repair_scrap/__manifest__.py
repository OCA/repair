# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Repair Scrap",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "category": "Repair",
    "summary": """To send to scrap components or irreparable components.""",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": [
        "repair_type",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/repair_order_view.xml",
        "views/stock_scrap_view.xml",
        "views/repair_type_views.xml",
        "wizards/repair_scrap_view.xml",
    ],
    "development_status": "Alpha",
    "installable": True,
}
