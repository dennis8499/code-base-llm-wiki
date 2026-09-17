from services.orders import summarize_order


ROUTES = {
    "POST /orders/drafts": "create_draft_order",
    "GET /orders/{order_id}/summary": "get_order_summary",
}


def create_draft_order(order_repository):
    return order_repository.create_draft()


def get_order_summary(order_id, order_repository):
    order = order_repository.get(order_id)
    if order is None:
        raise LookupError(order_id)
    return summarize_order(order)
