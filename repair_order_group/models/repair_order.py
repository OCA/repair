# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    """Extend repair.order with grouping, cascade, and shared quotation logic.

    Features added:
      • Link repairs into logical groups (via `repair.order.group`)
      • Automatically create groups when adding another repair
      • Synchronize customer (partner) across all repairs in the same group
      • Cascade confirmation/cancellation actions within the group
      • Create a single sale order for all repairs of one group
    """

    _inherit = "repair.order"

    group_id = fields.Many2one(
        "repair.order.group",
        string="Repair Group",
        check_company=True,
        index=True,
        readonly=True,
        copy=False,
        help="Repairs sharing the same group can be processed and quoted together.",
    )

    grouped_repair_ids = fields.One2many(
        "repair.order",
        compute="_compute_grouped_repair_ids",
        string="Grouped Repairs",
        help="All other repairs that belong to the same group.",
    )

    show_add_grouped_repair = fields.Boolean(
        compute="_compute_show_add_grouped_repair",
        help="Technical field used to control the Add Grouped Repair button.",
    )

    def _can_add_grouped_repair(self):
        """Return True if this repair can be added to a repair group."""
        self.ensure_one()
        allowed_states = set(
            self.company_id.sudo().add_grouped_repair_state_ids.mapped("value")
        )
        return self.state in allowed_states and self.sale_order_id.state not in (
            "sale",
            "cancel",
        )

    @api.depends(
        "state", "sale_order_id.state", "company_id.add_grouped_repair_state_ids"
    )
    def _compute_show_add_grouped_repair(self):
        for repair in self:
            repair.show_add_grouped_repair = repair._can_add_grouped_repair()

    @api.depends("group_id", "group_id.repair_ids")
    def _compute_grouped_repair_ids(self):
        """Compute other repairs in the same group (excluding current repair)."""
        for repair in self:
            if not repair.group_id:
                repair.grouped_repair_ids = False
                continue
            repair.grouped_repair_ids = repair.group_id.repair_ids - repair

    def action_add_another_repair(self):
        """Create a new empty repair linked to the same group.

        If the current repair is not yet assigned to a group, a new
        `repair.order.group` is automatically created first.
        The new repair will reuse basic logistics fields such as
        partner, company, and locations, but not copy any parts or products.
        """
        self.ensure_one()

        if not self._can_add_grouped_repair():
            raise UserError(
                self.env._(
                    "You cannot add a grouped repair in the current repair "
                    "state or when the related sale order is confirmed "
                    "or cancelled."
                )
            )

        if not self.group_id:
            self.group_id = self.env["repair.order.group"].create({})

        new_repair = self.env["repair.order"].create(
            {
                "group_id": self.group_id.id,
                "partner_id": self.partner_id.id,
                "company_id": self.company_id.id,
                "picking_type_id": self.picking_type_id.id,
                "location_id": self.location_id.id,
                "location_dest_id": self.location_dest_id.id,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.order",
            "res_id": new_repair.id,
            "view_mode": "form",
            "target": "current",
        }

    def write(self, vals):
        """Propagate partner changes across all repairs in the same group.

        When a user changes the partner on one repair, all other repairs
        of the same group automatically receive the same partner, ensuring
        data consistency. Recursion is prevented via the context flag
        `skip_group_sync`.

        All related repairs are updated in a single write operation.
        """
        res = super().write(vals)
        if "partner_id" in vals and not self.env.context.get("skip_group_sync"):
            # Exclude current records to avoid redundant writes
            repairs_to_process = self.mapped("grouped_repair_ids") - self
            if repairs_to_process:
                repairs_to_process.with_context(skip_group_sync=True).write(
                    {"partner_id": vals["partner_id"]}
                )
        return res

    def _post_create_grouped_hook(self):
        """
        Extension hook called after grouped sale orders are created.

        This hook is for adding extra functionality (like services, warranties, fees)
        to grouped sale orders. It does not replace the standard line creation logic
        which remains in action_create_sale_order().

        Modules extending repair_order_group should override this method to add
        their specific lines to sale orders created for grouped repairs.
        """
        return

    def _action_repair_confirm(self):
        """Confirm repairs and cascade confirmation to other group members.

        The original method is called once on the combined set of selected repairs
        and their group members to preserve all Odoo core logic and side effects.
        """
        if self.env.context.get("skip_group_confirm"):
            return super()._action_repair_confirm()

        # Collect ALL repairs to confirm: selected + their group members
        group_repairs = self.mapped("grouped_repair_ids")
        all_repairs = (self | group_repairs).with_context(skip_group_confirm=True)

        # Prevent calling the original method on an empty recordset
        if not all_repairs:
            return True

        # Single call to original method to preserve full Odoo workflow
        return super(RepairOrder, all_repairs)._action_repair_confirm()

    def action_repair_cancel(self):
        """Cancel repairs and cascade cancellation to other group members.

        The original method is called once on the combined set of selected repairs
        and their group members to preserve all Odoo core logic and side effects.
        """
        if self.env.context.get("skip_group_cancel"):
            return super().action_repair_cancel()

        # Collect ALL repairs to cancel: selected + their group members
        group_repairs = self.mapped("grouped_repair_ids").filtered(
            lambda r: r.state not in ("cancel", "done")
        )
        all_repairs = (self | group_repairs).with_context(skip_group_cancel=True)

        # Prevent calling the original method on an empty recordset
        if not all_repairs:
            return True

        # Single call to original method to preserve full Odoo workflow
        return super(RepairOrder, all_repairs).action_repair_cancel()

    def _get_valid_repairs_for_so(self):
        """
        Return the subset of repairs eligible for inclusion in a sale order.

        A repair is considered valid if it is not cancelled. Repairs already
        linked to sale orders are NOT filtered out here, as the module supports
        incremental quoting (multiple sale orders per group over time).
        The sale_order_id existence check is performed separately during validation.
        """
        return self.filtered(lambda r: r.state != "cancel")

    def action_create_sale_order(self):
        """Create Sale Order - single one for group or standard behavior if no group.

        For repair groups: creates one sale order containing all valid repairs
        from the same group. Maintains core Odoo validations while extending
        functionality for grouped repairs.

        Features:
        • Consolidated SO creation for repair groups
        • Standard individual SO creation for non-grouped repairs
        • Mixed selection handling with focused UX
        • Detailed validation messages with repair order references

        Returns:
            dict: Action to view the created sale order(s)
        """

        # Split selected repairs into grouped and ungrouped
        grouped = self.filtered(lambda r: r.group_id)
        ungrouped = self - grouped

        # No groups at all -> fallback to core logic
        if not grouped:
            return super().action_create_sale_order()

        # Core validations (same as original Odoo, but applied once)
        concerned = self.filtered("sale_order_id")
        if concerned:
            ref_str = "\n".join(concerned.mapped("name"))
            raise UserError(
                self.env._(
                    "You cannot create a quotation for a repair order that is "
                    "already linked to an existing sale order.\n"
                    "Concerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                )
            )

        no_partner = self.filtered(lambda ro: not ro.partner_id)
        if no_partner:
            ref_str = "\n".join(no_partner.mapped("name"))
            raise UserError(
                self.env._(
                    "You need to define a customer for a repair order in order to "
                    "create an associated quotation.\n"
                    "Concerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                )
            )

        so_vals_list = []

        # One Sale Order per unique repair group
        for _group in grouped.group_id:
            valid_repairs = _group.repair_ids._get_valid_repairs_for_so()

            if not valid_repairs:
                continue

            # Group repairs by warehouse ID
            repairs_by_warehouse = {}
            for repair in valid_repairs:
                warehouse_id = (
                    repair.picking_type_id.warehouse_id.id
                    if repair.picking_type_id.warehouse_id
                    else 0
                )
                wh_repairs = repairs_by_warehouse.get(warehouse_id)
                repairs_by_warehouse[warehouse_id] = (
                    wh_repairs | repair if wh_repairs else repair
                )

            # Create a separate SO per warehouse ID
            for warehouse_id, repairs in repairs_by_warehouse.items():
                if repairs._link_to_existing_group_sale_order():
                    continue

                so_vals_list.append(
                    {
                        "company_id": _group.company_id.id,
                        "partner_id": _group.partner_id.id,
                        "warehouse_id": warehouse_id if warehouse_id else False,
                        "repair_order_ids": [(4, repair.id) for repair in repairs],
                    }
                )

        # Bulk create all SOs for grouped repairs
        if so_vals_list:
            sale_orders = self.env["sale.order"].create(so_vals_list)
            sale_orders.repair_order_ids.move_ids._create_repair_sale_order_line()
            sale_orders.repair_order_ids._post_create_grouped_hook()

        # Create individual SOs for ungrouped repairs
        valid_ungrouped = ungrouped._get_valid_repairs_for_so()
        if valid_ungrouped:
            super(RepairOrder, valid_ungrouped).action_create_sale_order()

        # Return standard action - it will find all SOs linked to repairs
        return self.action_view_sale_order()

    def _link_to_existing_group_sale_order(self):
        """Link repairs without SO to the existing open group quotation."""
        sale_orders = self.sale_order_id.filtered(
            lambda so: so.state not in ("sale", "cancel")
        )
        if not sale_orders:
            return False

        if len(sale_orders) > 1:
            ref_str = "\n".join(self.filtered("sale_order_id").mapped("name"))
            raise UserError(
                self.env._(
                    "Several open sale orders are already linked to repair "
                    "orders from the same repair group and warehouse.\n"
                    "Concerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                )
            )

        repairs_to_add = self.filtered(lambda repair: not repair.sale_order_id)
        if repairs_to_add:
            sale_orders.write(
                {"repair_order_ids": [(4, repair.id) for repair in repairs_to_add]}
            )
            repairs_to_add.move_ids._create_repair_sale_order_line()
            repairs_to_add._post_create_grouped_hook()

        return True
