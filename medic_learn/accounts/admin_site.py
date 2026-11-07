from django.contrib.admin import AdminSite
from django.shortcuts import redirect


class CognitoAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        return redirect("/login/?next=/admin/")
