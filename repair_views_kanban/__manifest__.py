{
    "name": "Repair Views Kanban",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "Repair",
    "summary": "Mobile-optimized kanban views for repair orders",
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": ["repair"],
    "data": [
        "views/repair_views_kanban.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "repair_views_kanban/static/src/js/list_renderer_mobile.js",
        ],
    },
    "installable": True,
    "application": False,
}
