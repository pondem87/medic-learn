from .models import User


def locked_account(account_id):
    return User.objects.select_for_update().get(pk=account_id)
