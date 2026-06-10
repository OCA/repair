## 1) Create a Preparation location
1. Go to **Inventory / Configuration / Locations**
2. Create an **Internal** location (e.g. **WH/Preparation**)

## 2) Create a Preparation operation type
1. Go to **Inventory / Configuration / Operation Types**
2. Create a picking type named **Repair Preparation**
3. Set:
   - **Default Source Location** = *Your Warehouse/Stock*
   - **Default Destination Location** = *Your Warehouse/Preparation*

## 3) Route & Rule (Stock → Preparation)
1. Go to **Inventory / Configuration / Routes** and create **Route to Preparation**
2. Enable **Selectable on warehouse**
3. Add a **Pull Rule**:
   - **Action**: *Pull From*
   - **Operation Type**: *Preparation* (from step 2)
   - **Source Location**: *Your Warehouse/Stock*
   - **Destination Location**: *Your Warehouse/Preparation*
   - **Warehouse**: your warehouse

## 4) Warehouse settings (enable & default)
1. Go to **Inventory / Configuration / Warehouses**, open your warehouse
2. In **Technical info** tab, under **Repairs — Preparation**:
   - Tick **Enable Repair Preparation**
   - Set **Default Preparation Operation Type** to the *Repair Preparation* picking type created earlier

> You can enable/disable the feature per warehouse. The default picking type is used for new repairs governed by that warehouse and can still be overridden per repair.
