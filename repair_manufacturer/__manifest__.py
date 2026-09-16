{
    "name": "Repair Manufacturer",
    "summary": """Add Manufacturer for electronic devices""",
    "version": "18.0.1.0.0",
    "category": "Services/Repair",
    "author": "Coder4web, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": [
        "repair",
    ],
    "data": [
        "views/repair_order_menu.xml",
        "views/res_partner_view.xml",
        "views/repair_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
