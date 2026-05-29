This module introduces an optional intermediate step:

- When enabled at warehouse level, repair consumption moves are grouped
  into a stock picking.
- The repair order is set to a new **Consumption** state until the picking
  is validated.
- Users can process the picking manually, assign lots/serials, and only
  then complete the repair.