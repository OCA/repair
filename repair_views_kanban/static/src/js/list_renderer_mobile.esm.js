/** @odoo-module **/

import {ListRenderer} from "@web/views/list/list_renderer";
import {patch} from "@web/core/utils/patch";

patch(ListRenderer.prototype, "repair_views_kanban.ListRenderer", {
    /**
     * Override setDefaultColumnWidths to provide mobile-responsive behavior
     * specifically for repair models
     */
    setDefaultColumnWidths() {
        // Always call the original method first
        this._super(...arguments);

        // Then apply our mobile optimizations if needed
        const isMobile = window.innerWidth <= 768;
        const isRepairModel =
            this.props.list.resModel && this.props.list.resModel.startsWith("repair");

        if (isMobile && isRepairModel) {
            console.log("Aplicando optimización móvil para repair");
            // Use setTimeout to ensure DOM is ready
            setTimeout(() => {
                this.setMobileRepairColumnWidths();
            }, 0);
        }
    },

    /**
     * Set mobile-optimized column widths for repair models
     */
    setMobileRepairColumnWidths() {
        const columns = this.state.columns;
        if (columns.length === 0) return;

        console.log("Aplicando anchos auto-ajustables para repair móvil");

        // Set table to auto layout for content-based sizing
        if (this.tableRef.el) {
            this.tableRef.el.style.tableLayout = "auto";
            this.tableRef.el.style.width = "100%";
        }

        const columnOffset = this.hasSelectors ? 2 : 1;

        // Apply mobile-optimized widths based on content and field type
        columns.forEach((column, i) => {
            const headerEl = this.tableRef.el.querySelector(
                `th:nth-child(${i + columnOffset})`
            );
            if (!headerEl) return;

            // Remove any fixed width constraints
            headerEl.style.width = "auto";
            headerEl.style.minWidth = "auto";
            headerEl.style.maxWidth = "none";

            if (column.type === "field") {
                const fieldType =
                    column.widget || this.props.list.fields[column.name].type;
                console.log(`Columna ${i}: ${column.name} (${fieldType})`);

                switch (fieldType) {
                    case "many2one":
                        // Set reasonable constraints for many2one
                        headerEl.style.minWidth = "80px";
                        headerEl.style.maxWidth = "150px";
                        break;
                    case "char":
                    case "text":
                        // Allow text fields to expand but set reasonable limits
                        headerEl.style.minWidth = "120px";
                        headerEl.style.maxWidth = "250px";
                        break;
                    case "float":
                    case "integer":
                    case "monetary":
                        // Numeric fields stay compact
                        headerEl.style.minWidth = "60px";
                        headerEl.style.maxWidth = "100px";
                        break;
                    case "boolean":
                        // Boolean fields very compact
                        headerEl.style.minWidth = "40px";
                        headerEl.style.maxWidth = "60px";
                        break;
                    case "date":
                    case "datetime":
                        // Date fields moderate width
                        headerEl.style.minWidth = "80px";
                        headerEl.style.maxWidth = "120px";
                        break;
                    default:
                        // Default flexible sizing
                        headerEl.style.minWidth = "80px";
                        headerEl.style.maxWidth = "200px";
                        break;
                }
            }

            // Ensure headers can adjust to their text content
            headerEl.style.whiteSpace = "nowrap";
            headerEl.style.overflow = "visible";
            headerEl.style.textOverflow = "clip";
        });

        // Apply same logic to body cells for consistency
        const bodyRows = this.tableRef.el.querySelectorAll("tbody tr");
        bodyRows.forEach((row) => {
            const cells = row.querySelectorAll("td");
            cells.forEach((cell, i) => {
                if (i >= columnOffset - 1) {
                    // Adjust for selector offset
                    const columnIndex = i - (columnOffset - 1);
                    const column = columns[columnIndex];

                    if (column && column.type === "field") {
                        const fieldType =
                            column.widget || this.props.list.fields[column.name].type;

                        // Apply consistent sizing to body cells
                        cell.style.overflow = "hidden";
                        cell.style.textOverflow = "ellipsis";

                        if (fieldType === "boolean") {
                            cell.style.textAlign = "center";
                        }
                    }
                }
            });
        });
    },
});
