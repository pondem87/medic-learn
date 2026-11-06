from smtplib import SMTPRecipientsRefused, SMTPSenderRefused

from django.conf import settings
from django.core.mail import send_mail

from medic_learn.messages.contracts import ChannelRejected


class EmailChannel:
    def send(self, recipient: str, subject: str, body: str) -> str:
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except (SMTPRecipientsRefused, SMTPSenderRefused) as exc:
            raise ChannelRejected("SMTP rejected submission") from exc
        return ""
