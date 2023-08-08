import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-repair",
    description="Meta package for oca-repair Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-repair_reason>=15.0dev,<15.1dev',
        'odoo-addon-repair_refurbish>=15.0dev,<15.1dev',
        'odoo-addon-repair_refurbish_repair_stock_move>=15.0dev,<15.1dev',
        'odoo-addon-repair_stock_move>=15.0dev,<15.1dev',
        'odoo-addon-repair_type>=15.0dev,<15.1dev',
        'odoo-addon-repair_type_refurbish>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
