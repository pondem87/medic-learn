# Application architecture

## 1 Components

HTML forms/views and REST serializers/views call shared account and verification operations.
Accounts owns identity/profile state. Verification owns codes and generation controls.
Events owns durable envelopes and broker delivery. Notifications decides welcome-message eligibility.
Messages owns dispatch; SMTP and WhatsApp implement the channel protocol.

## 2 Flows

1. Registration creates account/profile transactionally, then issues and sends email proof.
2. Verification reserves an attempt; valid consumption, activation and event insertion are atomic.
3. Worker publishes outbox, consumes/deduplicates events, captures notifications, and queues messages.
4. Dispatcher claims each message before external I/O; acceptance is distinct from delivery.

## 3 Boundaries and failures

Django adapters return safe codes/errors. Provider exceptions are not serialized.
Database/broker failures leave pending outbox work retryable; malformed consumer work dead-letters.
Profile roles never grant access to unverified or blocked accounts.
The Python/Django boundary tradeoff is explicit in [ADR-001](decisions/001-django-foundation.md).

## 4 Limits

The WhatsApp adapter sends approved templates and records inbound observations/statuses.
It does not authenticate senders or execute inbound business actions. Media imports are deferred.
