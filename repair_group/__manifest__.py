# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Repair Group",
    "summary": "Create a group of repairs selecting Stock pickings",
    "version": "18.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Grupo Isonor, Odoo Community Association (OCA)",
    "maintainers": ["abelsrzz"],
    "license": "LGPL-3",
    "development_status": "Alpha",
    "depends": [
        "repair",
        "sale",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/repair_group_sequence.xml",
        "views/wizard_repair_group_quotation.xml",
        "views/repair_groups.xml",
        "views/repair_groups_menu.xml",
        "views/stock_picking_views.xml",
        "views/sale_order_views.xml",
        "views/repair_order_views.xml",
    ],
    "application": False,
    "installable": True,
    "post_init_hook": "post_init_hook",
}
