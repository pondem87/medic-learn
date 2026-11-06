from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from medic_learn.accounts import api, views
from medic_learn.whatsapp.views import webhook

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/form.html", extra_context={"title": "Sign in"}
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("verify/", views.verify, name="verify"),
    path("verify/resend/", views.resend, name="resend"),
    path("profile/", views.profile, name="profile"),
    path("profile/submit/", views.submit, name="submit"),
    path("staff/", views.staff, name="staff"),
    path("webhooks/whatsapp/", webhook),
    path("api/v1/auth/register/", api.RegisterView.as_view()),
    path("api/v1/auth/token/", api.LoginView.as_view()),
    path("api/v1/auth/token/refresh/", api.RefreshView.as_view()),
    path("api/v1/auth/logout/", api.LogoutView.as_view()),
    path("api/v1/auth/verify/", api.VerifyView.as_view()),
    path("api/v1/auth/resend/", api.ResendView.as_view()),
    path("api/v1/me/", api.ProfileView.as_view()),
    path("api/v1/accounts/<uuid:user_id>/actions/", api.ActionView.as_view()),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
