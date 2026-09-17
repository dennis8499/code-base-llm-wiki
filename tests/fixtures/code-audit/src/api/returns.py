from services.returns import create_return


ROUTES = {
    "POST /orders/{order_id}/return": "return_order_route",
}


def return_order_route(order_id, order_repository, days_since_purchase):
    order = order_repository.get(order_id)
    if days_since_purchase > 30:
        raise ValueError("return window expired")
    return create_return(order)
