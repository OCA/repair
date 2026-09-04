=========================
Repair IMEI Customization
=========================

This module extends Odoo's standard features to manage mobile and electronic device repairs by introducing mandatory IMEI tracking capabilities for customer-owned devices. Because these items are typically brought in directly by customers rather than pulled from internal stock (which uses `lot_id`), a dedicated character field is utilized. The module injects structured validation handlers into categories, product templates, and repair workflow orders to enforce global hardware uniqueness, prevent unauthorized duplication, and eliminate format errors during equipment servicing operations.

**Table of contents**

.. contents::
   :local:

Configuration
=============

To configure this module:

1. Navigate to **Inventory > Configuration > Products > Product Categories**.
2. Select or create a target category.
3. Enable the **IMEI Mandatory** field restriction to require checking rules for linked items.

Usage
=====

To utilize this module:

1. Go to the **Repair** application module dashboard.
2. Create a new **Repair Order**.
3. Select an article belonging to an IMEI-tracked category.
4. Input the customer-owned device's identifier into the dedicated **IMEI Number** input field.
5. The system automatically normalizes input, validates compliance against the Luhn checksum layout constraints, and enforces global hardware uniqueness across all active repair orders in the database.

Changelog
=========

18.0.1.0.0
----------

* Initial release of the Repair IMEI Customization module.
* Implemented strict structural manifest declarations, automated data normalization, and global uniqueness checks following OCA design specifications.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/repair/issues>`_.
In case of trouble, please check there if your issue has already been reported.

Maintainer
==========

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the Odoo Community Association (OCA).

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.