class Order:
    def __init__(self, order_id, total, line_count):
        self.id = order_id
        self.total = total
        self.line_count = line_count


class OrderRepository:
    def __init__(self):
        self._orders = {}

    def create_draft(self):
        order = Order("draft-1", total=0, line_count=0)
        self._orders[order.id] = order
        return order.id

    def get(self, order_id):
        return self._orders.get(order_id)
