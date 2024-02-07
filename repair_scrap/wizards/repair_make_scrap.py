# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairMakeScrap(models.TransientModel):
    _name = "repair_make_scrap.wizard"
    _description = "Wizard to create scrap from repair"

    item_ids = fields.One2many(
        comodel_name="repair_make_scrap_item.wizard",
        inverse_name="wiz_id",
        string="Items",
    )

    @api.returns("repair.order")
    def _prepare_item(self, line):
        values = {
            "product_id": line.product_id.id,
            "product_qty": line.product_qty,
            "location_id": line.location_id.id,
            "scrap_location_id": line.repair_type_id.scrap_location_id.id,
            "uom_id": line.product_id.uom_id.id,
            "repair_id": line.id,
            "lot_id": line.lot_id.id,
        }
        return values

    @api.model
    def default_get(self, fields_list):
        context = self._context.copy()
        res = super(RepairMakeScrap, self).default_get(fields_list)
        repair_obj = self.env["repair.order"]
        repair_ids = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]

        if not repair_ids:
            return res
        assert active_model == "repair.order", "Bad context propagation"

        items = []
        lines = repair_obj.browse(repair_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res["item_ids"] = items
        context.update({"items_ids": items})
        return res

    def _create_scrap(self):
        scraps = []
        for item in self.item_ids:
            repair = item.repair_id
            if repair.state == "draft" or repair.state == "cancel":
                raise ValidationError(_("Repair %s is not confirmed") % repair.name)
            scrap = self._prepare_scrap(item)
            scraps.append(scrap)
            item.repair_id.scrap_ids |= scrap
        return scraps

    def action_create_scrap(self):
        self._create_scrap()
        if self.item_ids:
            return self.item_ids[0].repair_id.action_view_scrap_transfers()

    @api.model
    def _prepare_scrap(self, item):
        repair = item.repair_id
        scrap = self.env["stock.scrap"].create(
            {
                "name": repair.id and repair.name,
                "origin": repair.name,
                "product_id": item.product_id.id,
                "scrap_qty": item.product_qty,
                "product_uom_id": item.product_id.product_tmpl_id.uom_id.id,
                "lot_id": item.lot_id.id,
                "location_id": item.location_id.id,
                "scrap_location_id": item.scrap_location_id.id,
                "repair_id": repair.id,
                "create_date": fields.Datetime.now(),
                "company_id": item.company_id.id,
                "is_repair_scrap": True,
            }
        )
        return scrap


class RepairMakeScrapItem(models.TransientModel):
    _name = "repair_make_scrap_item.wizard"
    _description = "Items to Scrap"

    def get_repair(self):
        repair_ids = self.env.context["active_ids"] or []
        if not repair_ids:
            return False
        return self.env["repair.order"].browse(repair_ids)

    @api.model
    def _default_repair_id(self):
        repair = self.get_repair()
        return repair.id

    @api.model
    def _default_location_id(self):
        repair = self.get_repair()
        return repair.location_id.id

    @api.model
    def _default_scrap_location_id(self):
        repair = self.get_repair()
        return repair.repair_type_id.scrap_location_id.id

    wiz_id = fields.Many2one("repair_make_scrap.wizard", string="Wizard", required=True)
    repair_id = fields.Many2one(
        "repair.order",
        string="repair Order",
        ondelete="cascade",
        required=True,
        default=lambda self: self._default_repair_id(),
    )
    product_id = fields.Many2one("product.product", string="Product", required=True)
    product_qty = fields.Float(
        string="Quantity Ordered",
        copy=False,
        digits="Product Unit of Measure",
    )
    company_id = fields.Many2one("res.company", related="repair_id.company_id")
    location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        default=lambda self: self._default_location_id(),
    )
    scrap_location_id = fields.Many2one(
        "stock.location",
        string="Scrap Location",
        required=True,
        domain="[('scrap_location', '=', True)]",
        default=lambda self: self._default_scrap_location_id(),
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    lot_id = fields.Many2one("stock.production.lot", string="Lot/Serial")
