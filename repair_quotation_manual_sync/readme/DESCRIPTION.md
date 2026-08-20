This module introduces synchronization logic between Repair Orders and the related Quotations.


1. Adds an "Invoiceable" checkbox on lines of a repair order to determine which products are billable.
2. Only lines marked as "Invoiceable" are included when creating the quotation.
3. Any changes in the Repair Order will trigger a banner in the quotation if there is a mismatch.
4. An "Synchronize Lines" button in the banner allows syncing the quotation lines with the lines indicated  as "Invoiceable" in the repair order.
