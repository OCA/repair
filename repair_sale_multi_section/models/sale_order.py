from collections import OrderedDict

from odoo import api, models
from odoo.fields import Command


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_create_repair_sections(self):
        for sale in self:
            if not sale.repair_order_ids:
                continue
            num_sections = len(
                sale.order_line.filtered(
                    lambda sale_line: sale_line.display_type == "line_section"
                )
            )
            num_repairs = len(sale.repair_order_ids)
            has_other_lines = any(
                not sale_line.repair_order_id and not sale_line.display_type
                for sale_line in sale.order_line
            )
            expected_sections = num_repairs + (1 if has_other_lines else 0)
            if num_sections == expected_sections:
                continue

            sale_lines = sale.order_line.sorted(
                key=lambda sale_line: (
                    sale_line.repair_order_id.id if sale_line.repair_order_id else 0,
                    sale_line.sequence,
                )
            )
            section_grouping_matrix = OrderedDict()
            for repair in sale.repair_order_ids:
                section_grouping_matrix.setdefault(repair, [])
            for sale_line in sale_lines:
                if sale_line.display_type:
                    continue
                group = sale_line.repair_order_id or False
                section_grouping_matrix.setdefault(group, []).append(sale_line)

            new_lines = []
            sequence = 10
            for group, lines in section_grouping_matrix.items():
                section_name = self._get_sale_section_name(group if group else None)
                new_lines.append(
                    Command.create(
                        {
                            "name": section_name,
                            "display_type": "line_section",
                            "sequence": sequence,
                            "repair_order_id": group.id if group else False,
                        }
                    )
                )
                sequence += 10
                for sale_line in lines:
                    new_lines.append(
                        Command.update(sale_line.id, {"sequence": sequence})
                    )
                    sequence += 10

            sale.order_line = new_lines

        return self

    def _get_sale_section_name(self, repair):
        return repair.name if repair else "Other"

    def _get_ordered_sale_lines(self):
        return self.order_line.sorted(
            key=lambda sale_line: (
                sale_line.repair_order_id.id if sale_line.repair_order_id else 0,
                sale_line.sequence,
            )
        )

    @api.model
    def _get_section_ordering(self):
        return (
            lambda sale_line: sale_line.repair_order_id.id
            if sale_line.repair_order_id
            else 0
        )
