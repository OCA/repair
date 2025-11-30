import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-repair",
    description="Meta package for oca-repair Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_repair_config>=16.0dev,<16.1dev',
        'odoo-addon-repair_calendar_view>=16.0dev,<16.1dev',
        'odoo-addon-repair_comment_template>=16.0dev,<16.1dev',
        'odoo-addon-repair_discount>=16.0dev,<16.1dev',
        'odoo-addon-repair_follow_lot_location>=16.0dev,<16.1dev',
        'odoo-addon-repair_picking_after_done>=16.0dev,<16.1dev',
        'odoo-addon-repair_purchase_return>=16.0dev,<16.1dev',
        'odoo-addon-repair_quality_control>=16.0dev,<16.1dev',
        'odoo-addon-repair_reason>=16.0dev,<16.1dev',
        'odoo-addon-repair_refurbish>=16.0dev,<16.1dev',
        'odoo-addon-repair_reinvoice>=16.0dev,<16.1dev',
        'odoo-addon-repair_sale_order>=16.0dev,<16.1dev',
        'odoo-addon-repair_security>=16.0dev,<16.1dev',
        'odoo-addon-repair_stock>=16.0dev,<16.1dev',
        'odoo-addon-repair_stock_move>=16.0dev,<16.1dev',
        'odoo-addon-repair_type>=16.0dev,<16.1dev',
        'odoo-addon-repair_type_refurbish>=16.0dev,<16.1dev',
        'odoo-addon-repair_type_sequence>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
