def cancel_account(account_id, account_repository):
    account = account_repository.get(account_id)
    if account is None:
        raise LookupError(account_id)
    account_repository.delete(account_id)
