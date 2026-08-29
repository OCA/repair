# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=missing-module-docstring

{
    "name": "Mobile IMEI Settings",
    "summary": "Add IMEI tracking and settings for mobile devices in repairs",
    "version": "18.0.1.0.0",
    "category": "Manufacturing/Repair",
    "author": "Coder4web, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": [
        "product",
        "repair",
    ],
    "data": [
        "views/repair_order_views.xml",
        "views/product_category_views.xml",
        "views/product_template_views.xml",
    ]
}
