# Local supporting services

Run from the project root:

```bash
docker compose --env-file .env -f docker/compose.yaml up -d --wait
docker compose --env-file .env -f docker/compose.yaml ps
docker compose --env-file .env -f docker/compose.yaml down
```

PostgreSQL: localhost:55432, database/user `medic`. RabbitMQ: localhost:5673,
management UI :15673. SMTP: localhost:1025; Mailpit inbox: localhost:8025.
Compose passwords and application connection URLs must match.
Named volumes preserve database/broker data across restarts. `down -v` destroys that data.
Image versions are pinned and should be updated deliberately after verification.

Django and its worker run through uv on the host. No MediaMTX placeholder service is started;
add it here when video-streaming requirements and storage/port choices are specified.

Production SMTP uses EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
EMAIL_USE_TLS and DEFAULT_FROM_EMAIL. TLS defaults off only for local Mailpit.
WhatsApp requires WHATSAPP_ENABLED, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID,
WHATSAPP_APP_SECRET, WHATSAPP_VERIFY_TOKEN and WHATSAPP_API_VERSION.
Only operator-provisioned English templates are supported by the initial adapter.
The template name is passed as the channel subject; free-text body is not sent through Meta.
Webhook URL: `/webhooks/whatsapp/`. Signed observations enter a durable database outbox;
HTTP 200 means persisted locally, not yet delivered through RabbitMQ.
