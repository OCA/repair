# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def post_init_hook(cr, _):
    # Delete the existing access rights
    cr.execute("""DELETE FROM ir_model_access WHERE name = 'repair.type.user'""")
    cr.execute("""DELETE FROM ir_model_access WHERE name = 'repair.type.manager'""")
