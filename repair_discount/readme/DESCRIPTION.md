This module adds a discount (%) on the part lines of repair orders.

Since Odoo 17.0, repair orders are no longer invoiced directly: billing
goes through a sale order linked to the repair. The discount set on a
part line is propagated to the discount of the corresponding sale order
line, both when the quotation is created from the repair order and when
parts are added to a repair already linked to a sale order.

Notes:

- The discount only applies to parts of type "Add", as they are the
  only ones billed on the sale order.
- Repairs under warranty ignore the discount (the parts are already
  invoiced at zero price).
- Repair fees do not exist anymore in the core `repair` module, so the
  discount on fee lines of previous versions has no equivalent.
