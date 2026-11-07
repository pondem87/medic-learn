from html.parser import HTMLParser

import pytest
from django.test import Client
from django.test.html import parse_html
from django.test.utils import override_settings
from django.urls import reverse

from medic_learn.accounts.models import User


class PageElements(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.links = []
        self.forms = []
        self.inputs = []
        self.feed(content.decode())

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a":
            self.links.append(attributes)
        elif tag == "form":
            self.forms.append(attributes)
        elif tag == "input":
            self.inputs.append(attributes)


@pytest.mark.parametrize("route", ["home", "register", "login"])
def test_public_pages_share_branding_and_valid_navigation(client, route):
    response = client.get(reverse(route))
    assert response.status_code == 200
    html = response.content.decode()
    parse_html(html)
    assert "MedEd Botswana" in html
    assert "Medic Learn" not in html
    page = PageElements(response.content)
    assert any(link.get("href") == "https://www.pfitztronic.co.bw" for link in page.links)
    assert any(link.get("href") == reverse("register") for link in page.links)
    assert all(link.get("href") and not link["href"].endswith(".html") for link in page.links)


def test_registration_errors_preserve_values_and_csrf():
    client = Client(enforce_csrf_checks=True)
    client.get(reverse("register"))
    response = client.post(
        reverse("register"),
        {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            "email": "invalid",
            "name": "Test learner",
            "role": "learner",
        },
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "Enter a valid email address." in html
    assert "This field is required." in html
    assert 'value="Test learner"' in html
    assert 'aria-invalid="true"' in html
    assert 'id="id_email_error"' in html
    assert 'name="csrfmiddlewaretoken"' in html


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("state", "staff", "route", "action"),
    [
        ("verified", False, "profile", "submit"),
        ("verified", True, "staff", None),
    ],
)
def test_account_pages_retain_post_forms_and_role_navigation(client, state, staff, route, action):
    user = User.objects.create_user("pages@example.com", "secret", state=state)
    if staff:
        user.is_staff = True
        user.save()
    client.force_login(user)
    response = client.get(reverse(route))
    assert response.status_code == 200
    html = response.content.decode()
    parse_html(html)
    assert "MedEd Botswana" in html
    assert "https://www.pfitztronic.co.bw" in html
    page = PageElements(response.content)
    assert all(form.get("method") == "post" for form in page.forms)
    tokens = [field for field in page.inputs if field.get("name") == "csrfmiddlewaretoken"]
    assert len(tokens) == len(page.forms)
    assert any(form.get("action") == reverse("logout") for form in page.forms)
    if action:
        assert any(form.get("action") == reverse(action) for form in page.forms)
    assert any(link.get("href") == reverse("staff") for link in page.links) == staff
    if state == "registered":
        assert not any(link.get("href") == reverse("profile") for link in page.links)


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["testserver"])
def test_sign_in_keeps_next_destination_and_errors(client):
    from unittest.mock import patch

    from medic_learn.accounts.domain import AccountError

    with (
        patch("medic_learn.accounts.web_auth.cipher"),
        patch(
            "medic_learn.accounts.cognito.authenticate",
            side_effect=AccountError("invalid", "Invalid credentials"),
        ),
    ):
        response = client.post(
            reverse("login") + "?next=/profile/",
            {"email": "login@example.com", "password": "incorrect", "next": "/profile/"},
        )
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert 'role="alert"' in response.content.decode()
    page = PageElements(response.content)
    assert any(
        field.get("name") == "next" and field["value"] == "/profile/" for field in page.inputs
    )
