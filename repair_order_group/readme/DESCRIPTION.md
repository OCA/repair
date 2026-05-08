This module allows users to group several repair orders and manage them in a
more convenient way.

Grouped repair orders are synchronized for the following actions:

- **Partner selection**: when a partner is changed in one repair order, the same
  partner is set on all other repair orders from the same group.
- **Order confirmation**: when one repair order is confirmed, all other repair
  orders from the same group are confirmed as well.
- **Order cancellation**: when one repair order is cancelled, all other repair
  orders from the same group are cancelled as well.
- **Quotation creation**: when a quotation is created, all repair orders from
  the same group are added to the same quotation.

The module also allows configuring the repair order states where the
**Add Grouped Repair** button is available. This is configured with the
**Available in** tags field in the Repair settings.

The button is always hidden when the related sales order is confirmed or
cancelled.
