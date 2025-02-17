# Copyright 2020-25 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Repair Refurbish",
    "summary": "Create refurbished products during repair",
    "version": "17.0.2.0.0",
    "category": "Manufacturing",
    "website": "https://github.com/OCA/repair",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["repair"],
    "data": [
        "views/repair_view.xml",
        "data/stock_data.xml",
        "views/product_template_view.xml",
        "views/product_product_view.xml",
    ],
}
