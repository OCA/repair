Adds analytic distribution to repair orders.

When a repair is completed, analytic journal entries are automatically created
for each part move, using the configured price type (sale price or cost) with
the following sign convention:

- **Added** parts → negative amount (cost)
- **Removed** parts → positive amount (recovery)
- **Recycled** parts → positive amount (recovery)

Entries are deleted on cancel or when the repair order is removed.
