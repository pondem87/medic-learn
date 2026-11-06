from typing import Protocol


class Channel(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> str: ...


class ChannelRejected(Exception):
    """Provider definitively rejected the submission; safe to classify as failed."""
