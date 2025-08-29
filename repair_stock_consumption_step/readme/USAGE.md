1. Create a repair order with spare part lines.
2. Confirm the repair order.
3. Click **End Repair**:
   - If the warehouse setting is disabled:
     - Consumption moves are validated immediately, repair goes directly to **Done**.
   - If the setting is enabled:
     - The repair order moves to the **Consumption** state.
     - A stock picking is created for the spare part moves.
4. Open the **Consumption Picking** from the repair order.
5. Process the picking:
   - Assign quantities and lots/serials.
   - Validate the picking.
6. Once the picking is validated, the repair order automatically moves to **Done**.