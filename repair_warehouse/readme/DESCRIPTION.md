This module adds a Warehouse field on Repair Orders to simplify
repair location selection in multi-warehouse environments.

When a repair location is chosen, the warehouse is automatically
determined and used to filter available locations. This makes
location selection clearer and avoids cross-warehouse mistakes.

A consistency rule ensures that the selected warehouse and
repair location always belong to the same warehouse.
