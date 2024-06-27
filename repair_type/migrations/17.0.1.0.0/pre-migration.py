# Copyright (C) 2024 APSL-Nagarro Antoni Marroig
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO stock_picking_type
        (create_date, default_add_location_dest_id, default_remove_location_dest_id,
        name,default_add_location_src_id, default_remove_location_src_id)
        SELECT create_date, destination_location_add_part_id,
        destination_location_remove_part_id, name,
        source_location_add_part_id, source_location_remove_part_id
        FROM repair_type;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE repair_order
        DROP COLUMN repair_type_id;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        DROP TABLE repair_type;
        """,
    )
