# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Analytic",
    "summary": "Adds analytic distribution to repair orders",
    "version": "18.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["repair", "analytic"],
    "data": [
        "views/stock_picking_type_views.xml",
        "views/repair_order_views.xml",
        "views/account_analytic_line_views.xml",
    ],
    "demo": [
        "demo/repair_analytic_demo.xml",
    ],
}
