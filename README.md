# MedEd Botswana

Django web and mobile API foundation for learners, trainers, and staff.
The current implementation provides email registration and verification, Cognito-backed web/mobile login,
profile review, account lifecycle management, and event-driven notification delivery.

## Setup

Run `uv sync --locked`, preserve the existing ignored `.env`, then start support
services with `docker compose --env-file .env -f docker/compose.yaml up -d --wait`.
Run `uv run python manage.py migrate`, `uv run python manage.py runserver`, and
`uv run python manage.py runworker` in another terminal.

Authentication requires separately configured AWS Cognito. Follow the
[Cognito deployment and cutover guide](infrastructure/README.md) for infrastructure,
secrets, explicit identity linking, staff bootstrap, registry choices and mobile PKCE.
Use the [staging deployment guide](infrastructure/staging/README.md) for live
signed-in testing with an isolated Cognito pool and containerized data services.
Do not use `createsuperuser` to create a local password; authentication is Cognito-only.
Existing passwords/sessions are invalidated by migration; account data is retained.

App: http://127.0.0.1:8000, Mailpit: http://127.0.0.1:8025,
RabbitMQ: http://127.0.0.1:15673. Mailpit handles application notifications;
Cognito sends identity emails. Missing Cognito settings fail login closed.

## Web templates

The home, registration, sign-in, verification, profile, and staff review pages share
the supplied HTML Codex eLearning theme. `templates/base.html` loads the common
styles and layout; `templates/components/` contains reusable navigation, footer,
hero, page header, feature cards, messages, and form fields.
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

Web uses Django sessions with custom Cognito registration, confirmation, sign-in,
password reset and optional authenticator MFA screens. Mobile uses Cognito managed
login with authorization code/PKCE; DRF accepts scoped Cognito access tokens.
See the [complete interface contract](infrastructure/README.md#web-and-mobile-contracts).

Accounts have one professional/student category. Pending users can manage onboarding
and their unverified bio. Approved students learn; approved professionals can switch
between learner and trainer. Staff permissions are independent. Staff alone populate
verified credentials, with reasons and activity history. Professional checks use a
Botswana registry; student checks use a private card upload. Cards are deleted after
approval/rejection. School contact and course delivery are deferred.

## Verification

```bash
terraform -chdir=infrastructure/terraform init -backend=false
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform test
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
Terraform prepares HTTPS, Fargate, RDS/MQ, private media and CloudFront static hosting.
Provisioning and deployment require the configured AWS account and a reviewed plan.
MediaMTX, course delivery, school contact and additional integrations are deferred.

## License

Not selected. Resolve ownership and licensing before distribution.
