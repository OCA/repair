The repair module consumes spare parts at the end of the repair without considering the quantity reservation.
the more natural flow is to have  a **staging step** to bring and reserve parts **before** the repair begins,
improving planning and reducing delays at the workbench.

This addon introduces a **Preparation** flow:
- On **Confirm** (validate) of the repair, a procurement is run procurement for all eligible **Add** lines
- When a repair line is **created/edited** while the repair is *Under Repair*:
  - If any linked move is **Done** → editing raises a validation error
  - Otherwise, linked moves are **canceled** and procurement is **re-run** for the updated lines
- **Finishing** a repair is blocked if:
  - There are consumed lines but **no preparation pickings**, or
  - Preparation pickings exist but are **not done**.