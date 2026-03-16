# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RepairGroup(models.Model):
    _name = "repair.group"
    _description = "Repair Group"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        "Repair Group Reference",
        default="New",
        copy=False,
        required=True,
        readonly=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        domain=[("type", "!=", "private")],
        tracking=True,
    )
    carrier_id = fields.Many2one(
        "res.partner",
        string="Carrier",
        domain=[("type", "!=", "private")],
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "New"),
            ("repairs_created", "Repairs Created"),
            ("quotation_requested", "Quotation Requested"),
            ("under_repair", "Under Repair"),
            ("done", "Repaired"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        copy=False,
        default="draft",
        readonly=True,
        tracking=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    supervisor_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    scheduled_datetime = fields.Datetime(string="Estimated date", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    internal_notes = fields.Html(sanitize=True)
    picking_ids = fields.One2many(
        "stock.picking",
        "repair_group_id",
        string="Delivery note",
    )
    repair_order_ids = fields.One2many(
        "repair.order",
        "repair_group_id",
        string="Repair Orders",
    )
    sale_order_ids = fields.Many2many(
        "sale.order", string="Sale Orders", compute="_compute_sale_order_ids"
    )
    complete_sale_order_id = fields.Many2one("sale.order", string="General Sale Order")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault(
                "name",
                self.env["ir.sequence"].sudo().next_by_code("repair.group") or "New",
            )
        res = super().create(vals_list)
        return res

    def action_create_all_repairs(self):
        Repair = self.env["repair.order"]

        for group in self:
            for picking in group.picking_ids:
                for move_line in picking.move_line_ids:
                    vals = {
                        "partner_id": group.partner_id.id,
                        "product_id": move_line.product_id.id,
                        "repair_group_id": group.id,
                    }
                    repair = Repair.create(vals)
                    move_line.write({"repair_order_id": repair.id})

        return self.write({"state": "repairs_created"})

    def action_return_to_draft(self):
        Repair = self.env["repair.order"]
        for group in self:
            for picking in group.picking_ids:
                for move_line in picking.move_line_ids:
                    if move_line.repair_order_id:
                        repair = Repair.browse(move_line.repair_order_id.id)
                        if repair.exists():
                            repair.action_repair_cancel()
                    move_line.write({"repair_order_id": False})

        return self.write({"state": "draft"})

    def action_request_quotations(self):
        for group in self:
            message = _("Quotations where requested.")
            group.message_post(body=message, subtype_xmlid="mail.mt_note")

            for repair_order in group.repair_order_ids:
                message = _("Quotation requested for this repair order.")
                repair_order.message_post(body=message, subtype_xmlid="mail.mt_note")

        return self.write({"state": "quotation_requested"})

    @api.depends("repair_order_ids.sale_order_id")
    def _compute_sale_order_ids(self):
        for group in self:
            sale_orders = self.env["sale.order"]
            for repair_order in group.repair_order_ids:
                if repair_order.sale_order_id:
                    sale_orders |= repair_order.sale_order_id
            group.sale_order_ids = sale_orders

    def action_create_complete_sale_order(self):
        self.ensure_one()
        if not self.sale_order_ids:
            raise UserError(_("No sale orders found to merge."))

        Wizard = self.env["repair.group.quotation.wizard"]
        wizard = Wizard.create({"repair_group_id": self.id})

        WizardLine = self.env["repair.group.quotation.wizard.line"]
        for repair_order in self.repair_order_ids:
            if repair_order.sale_order_id:
                WizardLine.create(
                    {
                        "wizard_id": wizard.id,
                        "sale_order_id": repair_order.sale_order_id.id,
                        "repair_order_id": repair_order.id,
                    }
                )

        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.group.quotation.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_confirm_complete_sale_order(self):
        for group in self:
            group.complete_sale_order_id.action_confirm()
        return self.write({"state": "under_repair"})

    def action_cancel_complete_sale_order(self):
        for group in self:
            group.complete_sale_order_id.action_cancel()
        return self.write({"state": "cancel"})

    def action_cancel_repair_group(self):
        return self.write({"state": "cancel"})

    def action_end_repair_group(self):
        Repair = self.env["repair.order"]
        for group in self:
            not_finished = []
            for picking in group.picking_ids:
                for move_line in picking.move_line_ids:
                    if move_line.repair_order_id:
                        repair = Repair.browse(move_line.repair_order_id.id)
                        if repair.exists() and repair.state != "done":
                            not_finished.append(
                                repair.display_name or repair.name or str(repair.id)
                            )
            if not_finished:
                raise UserError(
                    _(
                        "Cannot finish the group. The following repairs are not "
                        "finished: {}"
                    ).format(", ".join(not_finished))
                )

        return self.write({"state": "done"})
