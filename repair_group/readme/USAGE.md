## Creating a Repair Group from a Stock Picking

1. Open a **done** stock picking whose products are owned by a customer
   (Consignment must be enabled — this module enables it automatically on
   installation).
2. Click **Create Repair Group** in the picking form header.
3. The system creates a new repair group pre-filled with the customer and the
   picking. You are redirected to the repair group form.

## Repair Group Workflow

1. **Draft**: Add additional pickings if needed. Click **Create Repairs** to
   generate one repair order per move line.
2. **Repairs Created**: Review the generated repair orders in the *Repair Orders*
   tab. Click **Request Quotations** to move forward, or **Return to Draft** to
   undo.
3. **Quotation Requested**: Technicians fill in repair details and generate
   quotations from each repair order. Once all quotations exist, click **Create
   Complete Sale Order** to open the wizard.
4. **Wizard – Select Quotations**: Choose which quotations to merge and click
   **Create Complete Sale Order**. The system consolidates the selected lines
   into a single sale order.
5. **Quotation Requested (with main order)**: Review the consolidated order.
   Click **Confirm Complete Sale Order** to confirm it and move to *Under Repair*,
   or **Cancel Complete Sale Order** to discard it.
6. **Under Repair**: Repairs are being performed. Click **End Repair Group**
   once all repair orders are in *Done* state.
7. **Repaired**: The group is complete.

## Supervisor Approval

On each repair order that belongs to a group, the responsible user can click
**Request Approval** to submit it for supervisor validation. The supervisor
(configured on the repair group) can then **Validate** or **Reject** the repair
directly from the repair order form.
