# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class RepairOrder(models.Model):
    _inherit = "repair.order"

    preparation_picking_type_id = fields.Many2one(
        "stock.picking.type",
        help="Picking type used to bring spare parts before the repair starts.",
        domain="[('warehouse_id.company_id', '=', company_id)]",
        compute="_compute_preparation_picking_type_id",
        readonly=False,
        store=True,
    )
    preparation_group_id = fields.Many2one(
        "procurement.group",
        string="Preparation Procurement Group",
        readonly=True,
        copy=False,
        help="Procurement group used to gather all preparation moves/pickings.",
    )
    stock_move_ids = fields.Many2many("stock.move", compute="_compute_stock_move_ids")
    stock_moves_count = fields.Integer(compute="_compute_stock_move_ids")
    preparation_picking_ids = fields.Many2many(
        "stock.picking", compute="_compute_preparation_picking_ids"
    )
    preparation_pickings_count = fields.Integer(
        compute="_compute_preparation_picking_ids"
    )
    repair_preparation_enabled = fields.Boolean(
        compute="_compute_repair_preparation_enabled"
    )

    @api.depends("warehouse_id.repair_preparation_enabled", "location_id.usage")
    def _compute_repair_preparation_enabled(self):
        for rec in self:
            rec.repair_preparation_enabled = bool(
                rec.warehouse_id.repair_preparation_enabled
                and rec.location_id.usage != "customer"
            )

    @api.depends("warehouse_id", "repair_preparation_enabled")
    def _compute_preparation_picking_type_id(self):
        for rec in self:
            if rec.repair_preparation_enabled and not rec.preparation_picking_type_id:
                rec.preparation_picking_type_id = (
                    rec.warehouse_id.repair_preparation_picking_type_id
                )

    @api.depends("operations.preparation_move_ids", "operations.move_id")
    def _compute_stock_move_ids(self):
        for rec in self:
            rec.stock_move_ids = (
                rec.operations.preparation_move_ids + rec.operations.move_id
            )
            rec.stock_moves_count = len(rec.stock_move_ids)

    @api.depends("operations.preparation_move_ids")
    def _compute_preparation_picking_ids(self):
        for rec in self:
            rec.preparation_picking_ids = rec.operations.preparation_move_ids.picking_id
            rec.preparation_pickings_count = len(rec.preparation_picking_ids)

    def _ensure_preparation_group(self):
        self.ensure_one()
        if not self.preparation_group_id:
            self.preparation_group_id = self.env["procurement.group"].create(
                {
                    "name": _("Preparation for") + " " + self.name,
                    "partner_id": self.partner_id.id,
                }
            )

    @api.model
    def _get_consumed_lines_for_preparation(self, operations):
        return operations.filtered(
            lambda line: line.type == "add"
            and line.product_id
            and float_compare(
                line.product_uom_qty, 0.0, precision_rounding=line.product_uom.rounding
            )
            > 0
        )

    def _get_repair_line_procurement_values(self, line):
        return {
            "company_id": self.company_id,
            "group_id": self.preparation_group_id,
            "warehouse_id": self.preparation_picking_type_id.warehouse_id,
            "picking_type_id": self.preparation_picking_type_id.id,
            "repair_line_id": line.id,
        }

    def _get_repair_line_procurement(self, line):
        return self.env["procurement.group"].Procurement(
            line.product_id,
            line.product_uom_qty,
            line.product_uom,
            self.location_id,
            f"{self.name} {line.product_id.display_name}",
            self.name,
            self.company_id,
            self._get_repair_line_procurement_values(line),
        )

    def _run_preparation_procurements(self, operations):
        self.ensure_one()
        if not operations:
            return
        if not self.preparation_picking_type_id:
            return
        lines = self._get_consumed_lines_for_preparation(operations)
        if not lines:
            return
        self._ensure_preparation_group()
        self.env["procurement.group"].run(
            [self._get_repair_line_procurement(line) for line in lines]
        )

    def action_validate(self):
        """repairs performed at a customer location don't require a preparation flow
        and do not need to check available quantities (handled in super)"""
        customer_repairs = self.filtered(
            lambda repair: repair.location_id.usage == "customer"
        )
        non_customer_repairs = self.filtered(
            lambda repair: repair.location_id.usage != "customer"
        )
        res = customer_repairs.action_repair_confirm() if customer_repairs else True
        if not non_customer_repairs:
            return res
        res = super(RepairOrder, non_customer_repairs).action_validate()
        for repair in non_customer_repairs:
            if not repair.repair_preparation_enabled:
                continue
            repair._run_preparation_procurements(repair.operations)

        return res

    def action_repair_cancel(self):
        res = super().action_repair_cancel()
        if pickings_to_cancel := self.preparation_picking_ids.filtered(
            lambda p: p.state not in ("done", "cancel")
        ):
            pickings_to_cancel.action_cancel()
        return res

    def action_repair_end(self):
        for rec in self:
            if not rec.repair_preparation_enabled:
                continue
            consumed_lines = rec._get_consumed_lines_for_preparation(rec.operations)
            if consumed_lines and not rec.preparation_picking_ids:
                raise ValidationError(
                    _(
                        "Preparation picking not found. Please procure/prepare parts "
                        "first."
                    )
                )
            if consumed_lines and rec.preparation_picking_ids.filtered(
                lambda p: p.state != "done"
            ):
                raise ValidationError(
                    _(
                        "Preparation picking is not done yet. Validate it before "
                        "starting the repair."
                    )
                )
        return super().action_repair_end()

    def action_view_preparation_picking(self):
        self.ensure_one()
        action_xmlid = "stock.action_picking_tree_all"
        action = self.env["ir.actions.act_window"]._for_xml_id(action_xmlid)
        action["domain"] = [("id", "in", self.preparation_picking_ids.ids)]
        return action

    def action_view_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Moves"),
            "res_model": self.stock_move_ids._name,
            "domain": [("id", "in", self.stock_move_ids.ids)],
            "view_mode": "tree,form",
            "context": self.env.context,
        }
