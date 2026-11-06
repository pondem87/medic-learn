from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "medic_learn.accounts"

    def ready(self):
        from . import schema

        return schema
