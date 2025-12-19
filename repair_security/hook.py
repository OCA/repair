def post_init_hook(env):
    # Giving Repair Admin access to match the previous permissions.
    env.ref("repair_security.group_repair_manager").write(
        {
            "user_ids": [(6, 0, env.ref("stock.group_stock_user").user_ids.ids)],
        }
    )
