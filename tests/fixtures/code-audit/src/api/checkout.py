from services.checkout import checkout


ROUTES = {
    "POST /checkout": "checkout_route",
}


def checkout_route(payload):
    quantity = int(payload["quantity"])
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    return checkout(quantity)
