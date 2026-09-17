from services.accounts import cancel_account


ROUTES = {
    "POST /accounts/{account_id}/cancel": "cancel_account_route",
}


def cancel_account_route(account_id, account_repository):
    return cancel_account(account_id, account_repository)
