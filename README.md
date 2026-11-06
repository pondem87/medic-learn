# MedEd Botswana

Django web and mobile API foundation for learners, trainers, and staff.
The current implementation provides email registration and verification, session/JWT login,
profile review, account lifecycle management, and event-driven notification delivery.

## Setup

Prerequisites: uv 0.12.21, Python 3.12.14, Docker Engine with Compose.
Run commands from this directory. Django runs on the host; supporting services run in Docker.

```bash
uv sync --locked
cp .env.example .env
# Replace DJANGO_SECRET_KEY and PROOF_KEY with separate random values.
# Generate each with: uv run python -c 'import secrets; print(secrets.token_urlsafe(48))'
docker compose --env-file .env -f docker/compose.yaml up -d --wait
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

An ignored `.env` with generated secrets has already been created in this workspace.
Do not overwrite it when continuing this installation. It contains local development credentials.
Start a separate terminal for the worker:

```bash
uv run python manage.py runworker
```

Visit the application at http://127.0.0.1:8000, Mailpit at http://127.0.0.1:8025,
and RabbitMQ management at http://127.0.0.1:15673 (local user `medic`).
Use `/staff/` for review/lifecycle actions; `/admin/` is a read-only account inspector.
Email verification codes appear only in the delivered email, not API responses.

## Web templates

The home, registration, sign-in, verification, profile, and staff review pages share
the supplied HTML Codex eLearning theme. `templates/base.html` loads the common
styles and layout; `templates/components/` contains reusable navigation, footer,
hero, page header, feature cards, account review cards, messages, and form fields.
Extend the base layout for new pages, or `templates/accounts/form.html` for account
forms using its `form_intro`, `submit_label`, and `form_footer` blocks. Include
components with explicit context; form-containing components also need the CSRF
context. All application links use named Django routes, including Join Now → registration.

Theme CSS and the images used by these pages are in `static/vendor/elearning/`,
alongside the supplied license and provenance. Keep upstream assets separate from
application overrides in `static/app.css` and mobile navigation in `static/app.js`.
The home carousel preserves the original template's Owl Carousel markup, image
sizing, animated buttons, arrow controls, and autoplay configuration. It loads
the supplied Owl Carousel and animation assets and the template's jQuery 3.4.1
dependency only on the home page. Bootstrap Icons uses the template's CDN URL.
Carousel initialization lives in `static/home-carousel.js`; mobile navigation
remains in `static/app.js`.
Google Fonts is optional; local
font fallbacks keep the pages usable if it is unavailable. No theme demo courses,
testimonials, contact form, or newsletter endpoints are introduced.
The shared footer credits [Pfitztronic](https://www.pfitztronic.co.bw).
The shared navigation and footer use `static/Meded_Botswana_Logo_Icon_150px.png`;
the favicon uses `static/Meded_Botswana_Logo_Icon_70px.png`. The home page introduces
the CME platform for doctors, nurses, and other health professionals, including
specialist training, CPD points, and wider, lower-cost distribution for trainers.
These describe the platform's intended offering; the current account foundation
does not yet implement training delivery or CPD tracking.

## Web and mobile interfaces

Web routes: `/register/`, `/login/`, `/verify/`, `/profile/`, `/staff/`.
All web mutations require POST and a CSRF token. Logout is POST-only.

Mobile routes under `/api/v1/`:

- `POST auth/register/`: email, password, name, learner/trainer role.
- `POST auth/token/`: email and password; returns access and refresh tokens.
- `POST auth/token/refresh/`: refresh token; rotates it.
- `POST auth/logout/`: refresh token; requires bearer authentication.
- `POST auth/verify/`: five-digit code; `POST auth/resend/` requests a new code.
- `GET/PATCH me/`: verified account profile and editable profile fields.
- `POST accounts/{uuid}/actions/`: submit, review, validate, return, role,
  suspended, disabled, deleted, restore, approve_verification, deny_verification.
  Review/lifecycle operations require a verified staff profile.

Send `Authorization: Bearer <access>` for protected API operations.
Registered accounts can access verification/resend/logout only.
JWT logout revokes the refresh token; an already-issued access token lasts up to five minutes.
Blocking an account invalidates both web sessions and all tokens immediately on their next use.
Schema: `/api/schema/`; interactive reference: `/api/docs/`.

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy medic_learn config
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
RUN_BROKER_TESTS=1 uv run pytest
uv run python manage.py spectacular --file /tmp/medic-schema.yaml --validate --fail-on-warn
uv run python manage.py collectstatic --noinput
uv run python scripts/check_docs.py
```

Tests use a separate Django test database on PostgreSQL. Broker tests require an idle,
dedicated development/test broker; do not run them against a shared environment.
CI runs the same checks using ephemeral PostgreSQL and RabbitMQ services.

## Standards and architecture

Active profile: [Python](profiles/python.md), applying to all Python source.
Read [architecture](ARCHITECTURE.md), [style](STYLE_GUIDE.md),
[contribution guidance](CONTRIBUTING.md), and [agent instructions](AGENTS.md).
Start project documentation with [the documentation guide](docs/000-docs-guide.md),
[description](docs/001-general-description.md), [requirements](docs/002-detailed-requirements.md),
and [decisions](docs/decisions/README.md).

## Operational limits

SMTP acceptance is not confirmed recipient delivery. Uncertain dispatches are not automatically
resent. Dead-letter messages require operator inspection; preserve event IDs during replay.
WhatsApp is disabled by default; configure the settings documented in [Docker setup](docker/README.md)
and an approved Meta template before use. No real provider credentials are bundled.
Production requires HTTPS, explicit hosts, external secrets, database/broker backup policy,
and a static-file serving arrangement. Production deployment is not included.
MediaMTX, password recovery, evidence uploads, retention jobs, and additional integrations are deferred.

## License

Not selected. Resolve ownership and licensing before distribution.
