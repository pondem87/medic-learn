from django.contrib.admin.apps import AdminConfig


class CognitoAdminConfig(AdminConfig):
    default_site = "medic_learn.accounts.admin_site.CognitoAdminSite"
