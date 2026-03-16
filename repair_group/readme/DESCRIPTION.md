This module allows grouping multiple repair orders by selecting completed stock
pickings (delivery notes) from a specific customer.

**Key features:**

- Create a **Repair Group** from one or more done stock pickings belonging to the
  same customer (consignment/owner-tracked pickings).
- Automatically generate individual repair orders for each product in the
  selected pickings.
- Supervisor approval workflow: technicians request approval and supervisors
  validate or reject each repair order.
- Merge individual repair quotations (sale orders) into a single consolidated
  sale order per group using a selection wizard.
- Full traceability: each repair order is linked to its origin picking move line
  and to the repair group.
- State tracking across the full lifecycle: *Draft → Repairs Created → Quotation
  Requested → Under Repair → Repaired* (or *Cancelled*).
- Mail thread and activity tracking on repair groups.
- Smart button on stock pickings to navigate directly to the associated repair
  group.
