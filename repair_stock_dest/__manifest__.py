# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Stock Destination",
    "summary": "Add destination field to a repair order",
    "version": "17.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Patryk Pyczko, Odoo Community Association (OCA)",
    "maintainers": ["ppyczko"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["repair"],
    "data": ["views/repair_views.xml", "views/stock_picking_type_views.xml"],
}
