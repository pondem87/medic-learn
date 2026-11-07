from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import evidence, services
from .domain import AccountError
from .forms import ProfileForm, ReviewForm, SubmissionForm
from .models import Activity, Evidence, Operation, User


def staff_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            services.require_staff(request.user)
        except AccountError:
            return HttpResponseForbidden()
        return view(request, *args, **kwargs)

    return wrapped


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        try:
            services.profile_update(request.user, form.cleaned_data)
            return redirect("profile")
        except (AccountError, ValidationError) as exc:
            form.add_error(None, str(exc))
    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "title": "Your profile",
            "submission_form": SubmissionForm(initial={"category": request.user.profile.category}),
            "roles": services.allowed_roles(request.user),
            "active_role": request.session.get("active_role", "learner"),
        },
    )


@login_required
@require_POST
def submit(request):
    form = SubmissionForm(request.POST, request.FILES)
    if form.is_valid():
        values = form.cleaned_data
        try:
            services.submit(
                request.user,
                values["category"],
                values["council"].pk if values["council"] else None,
                values["registration_number"],
                values["card"],
            )
            messages.success(
                request, "Submitted for staff review. Learning access requires approval."
            )
            return redirect("profile")
        except (AccountError, ValidationError) as exc:
            form.add_error(None, str(exc))
    return render(
        request,
        "accounts/submission.html",
        {"form": form, "title": "Submit verification"},
        status=400,
    )


@login_required
@require_POST
def switch_role(request):
    role = request.POST.get("role", "")
    try:
        with transaction.atomic():
            # Serialize selection against review updates; permissions are also rechecked per use.
            from .models import Profile

            Profile.objects.select_for_update().get(user=request.user)
            services.require_role(request.user, role)
            services.audit(
                request.user,
                request.user,
                "role.selected",
                before={"role": request.session.get("active_role", "learner")},
                after={"role": role},
            )
        request.session["active_role"] = role
    except AccountError as exc:
        messages.error(request, exc.message)
    return redirect("profile")


@staff_required
def staff(request):
    return render(
        request,
        "accounts/staff.html",
        {
            "accounts": User.objects.select_related("profile").order_by("email")[:100],
            "operations": Operation.objects.filter(completed_at=None).order_by("created_at")[:100],
        },
    )


@staff_required
def staff_detail(request, user_id):
    target = get_object_or_404(User.objects.select_related("profile"), pk=user_id)
    form = ReviewForm(
        request.POST or None,
        initial={**services.snapshot(target.profile), "council": target.profile.council_id},
    )
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy()
        action, reason, version = values.pop("action"), values.pop("reason"), values.pop("version")
        council = values.pop("council")
        values["council_id"] = council.pk if council else None
        try:
            services.review(request.user, target.pk, action, version, reason, values)
            messages.success(request, "Review saved.")
            return redirect("staff-detail", user_id=target.pk)
        except (AccountError, ValidationError) as exc:
            form.add_error(None, str(exc))
    return render(
        request,
        "accounts/review.html",
        {
            "form": form,
            "title": "Review profile",
            "target": target,
            "activities": Activity.objects.filter(subject=target).select_related("actor")[:200],
            "evidence": Evidence.objects.filter(user=target, available=True),
        },
    )


@staff_required
@require_POST
def staff_action(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    try:
        action, reason = request.POST.get("action"), request.POST.get("reason", "")
        if action == "reset_mfa":
            services.request_mfa_reset(request.user, target.pk, reason)
        elif action in {"suspended", "disabled", "deleted", "restore"}:
            services.account_action(request.user, target.pk, action, reason)
        else:
            raise AccountError("invalid_action", "Action is unavailable.")
    except AccountError as exc:
        messages.error(request, exc.message)
    return redirect("staff-detail", user_id=target.pk)


@staff_required
def download_evidence(request, evidence_id):
    with transaction.atomic():
        item = get_object_or_404(
            Evidence.objects.select_for_update(), pk=evidence_id, available=True
        )
        stream = evidence.read(item)
        services.audit(request.user, item.user, "evidence.viewed", after={"id": str(item.pk)})
    response = FileResponse(
        stream,
        as_attachment=True,
        filename="student-card" + (".pdf" if item.content_type == "application/pdf" else ".jpg"),
        content_type=item.content_type,
    )
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "sandbox"
    return response
