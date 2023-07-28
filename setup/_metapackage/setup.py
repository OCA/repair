import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-repair",
    description="Meta package for oca-repair Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-repair_picking_after_done>=16.0dev,<16.1dev',
        'odoo-addon-repair_type>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
