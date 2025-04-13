# Copyright 2025 Vicent Cubells - Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair Comments",
    "summary": "Comments templates on Repair documents",
    "version": "16.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Trey, Kilobytes de Soluciones, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["cubells"],
    "depends": [
        "base_comment_template",
        "repair",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/repair_order_views.xml",
        "views/base_comment_template_views.xml",
        "views/report_repairorder.xml",
    ],
    "installable": True,
}
