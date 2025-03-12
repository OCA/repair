This module ensures that when a kit product (with a BoM) is added to a repair order, it is correctly reflected in the corresponding sale order as a kit.

Key Features:

- When a kit product is added as a part of a repair order, its Bill of Materials (BoM) components are automatically exploded into separate stock moves. Instead of creating individual sale order lines for each component, this module groups them into a single sale order line for the original kit product when the sale order is generated.
- Ensures that delivered quantities in the sale order are correctly updated upon repair completion, counting only fully completed kits (where all required components are done in the repair).
