import httpx
from django.conf import settings

from medic_learn.messages.contracts import ChannelRejected


class WhatsAppChannel:
    def send(self, recipient: str, subject: str, body: str) -> str:
        if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_API_VERSION:
            raise ValueError("WhatsApp is not configured")
        # subject is an operator-provisioned approved template name.
        response = httpx.post(
            f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_ID}/messages",
            headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {"name": subject, "language": {"code": "en"}},
            },
            timeout=10,
            follow_redirects=False,
        )
        if 400 <= response.status_code < 500 and response.status_code != 408:
            raise ChannelRejected("WhatsApp rejected submission")
        response.raise_for_status()
        return str(response.json()["messages"][0]["id"])
