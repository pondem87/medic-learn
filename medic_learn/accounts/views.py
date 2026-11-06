from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from medic_learn.verification import services as verification

from . import services
from .domain import AccountError
from .forms import CodeForm, ProfileForm, RegistrationForm
from .models import User


def verified(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.state != "verified":
            return redirect("verify")
        return view(request, *args, **kwargs)

    return wrapped


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = services.register(**form.cleaned_data)
            verification.issue(user)
            login(request, user, backend="medic_learn.accounts.authentication.AccountBackend")
            return redirect("verify")
        except (AccountError, ValidationError) as exc:
            form.add_error(None, str(exc))
    return render(request, "accounts/form.html", {"form": form, "title": "Create account"})


@login_required
def verify(request):
    if request.user.state == "verified":
        return redirect("profile")
    form = CodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            verification.verify(request.user, form.cleaned_data["code"])
            return redirect("profile")
        except AccountError as exc:
            form.add_error(None, exc.message)
    return render(request, "accounts/verify.html", {"form": form, "title": "Verify email"})


@login_required
@require_POST
def resend(request):
    try:
        status = verification.issue(request.user)
        messages.info(request, f"Verification dispatch: {status}.")
    except AccountError as exc:
        messages.error(request, exc.message)
    return redirect("verify")


@verified
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        try:
            services.profile_update(request.user, form.cleaned_data)
            return redirect("profile")
        except (AccountError, ValidationError) as exc:
            form.add_error(None, str(exc))
    return render(request, "accounts/profile.html", {"form": form, "title": "Your profile"})


@verified
@require_POST
def submit(request):
    try:
        services.profile_action(request.user, request.user.pk, "submit")
    except AccountError as exc:
        messages.error(request, exc.message)
    return redirect("profile")


@verified
def staff(request):
    try:
        services.require_staff(request.user)
    except AccountError:
        return HttpResponseForbidden()
    if request.method == "POST":
        try:
            target = User.objects.get(pk=request.POST.get("user_id"))
            action = request.POST.get("action")
            if action in {"suspended", "disabled", "deleted", "restore"}:
                services.account_action(request.user, target.pk, action)
            elif action in {"approve_verification", "deny_verification"}:
                verification.review(request.user, target.pk, action == "approve_verification")
            else:
                services.profile_action(
                    request.user,
                    target.pk,
                    action,
                    request.POST.get("reason", ""),
                    request.POST.get("role", ""),
                )
        except (User.DoesNotExist, ValueError, ValidationError):
            raise Http404 from None
        except AccountError as exc:
            messages.error(request, exc.message)
        return redirect("staff")
    return render(
        request,
        "accounts/staff.html",
        {"accounts": User.objects.select_related("profile").order_by("email")[:100]},
    )
