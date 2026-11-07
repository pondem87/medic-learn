from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from medic_learn.accounts import api, views, web_auth
from medic_learn.whatsapp.views import webhook

urlpatterns = [
    path("health/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("register/", web_auth.register, name="register"),
    path("login/", web_auth.login, name="login"),
    path("logout/", web_auth.logout, name="logout"),
    path("verify/", web_auth.verify, name="verify"),
    path("verify/resend/", web_auth.resend, name="resend"),
    path("password/forgot/", web_auth.forgot, name="forgot-password"),
    path("password/reset/", web_auth.reset, name="reset-password"),
    path("mfa/challenge/", web_auth.mfa_challenge, name="mfa-challenge"),
    path("mfa/setup/", web_auth.mfa_setup, name="mfa-setup"),
    path("profile/", views.profile, name="profile"),
    path("profile/submit/", views.submit, name="submit"),
    path("profile/role/", views.switch_role, name="switch-role"),
    path("staff/", views.staff, name="staff"),
    path("staff/<uuid:user_id>/", views.staff_detail, name="staff-detail"),
    path("staff/<uuid:user_id>/action/", views.staff_action, name="staff-action"),
    path("staff/evidence/<uuid:evidence_id>/", views.download_evidence, name="evidence"),
    path("webhooks/whatsapp/", webhook),
    path("api/v1/councils/", api.CouncilView.as_view()),
    path("api/v1/me/submissions/", api.SubmissionView.as_view()),
    path("api/v1/me/", api.ProfileView.as_view()),
    path("api/v1/accounts/<uuid:user_id>/actions/", api.ActionView.as_view()),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
