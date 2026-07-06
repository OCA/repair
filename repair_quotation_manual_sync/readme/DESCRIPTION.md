This module makes the synchronization between a repair order and its
quotation an explicit action instead of an automatic one. In standard Odoo
every part added to or changed on a repair order is pushed to the linked
quotation straight away; here the quotation only changes when a user asks
for it, and each part carries an **Invoiceable** flag that decides whether
it reaches the quotation at all. Whenever the two documents drift apart, a
banner on the quotation reports it and offers a **Synchronize Lines** button
that brings the quotation in line with the repair order. Synchronization
applies to quotations that are still a draft or have been sent; the lines of
the quotation created from the repair order itself are filled in
automatically.
