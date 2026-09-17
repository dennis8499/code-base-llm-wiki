from services.orders import summarize_order


COMMANDS = {
    "orders summary": "order_summary_command",
}


def order_summary_command(order_id, order_repository):
    order = order_repository.get(order_id)
    if order is None:
        raise LookupError(order_id)
    return summarize_order(order)
