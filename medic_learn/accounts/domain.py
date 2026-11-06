from dataclasses import dataclass


class AccountError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


ELIGIBLE = {"registered", "verified"}
BLOCKED = {"suspended", "disabled", "deleted"}


@dataclass(frozen=True)
class AccountState:
    state: str
    previous: str = ""

    def transition(self, action: str) -> "AccountState":
        if self.state == "deleted":
            raise AccountError("invalid_state", "Deleted accounts cannot transition.")
        if (
            action == "restore"
            and self.state in {"suspended", "disabled"}
            and self.previous in ELIGIBLE
        ):
            return AccountState(self.previous)
        if action in {"suspended", "disabled", "deleted"} and action != self.state:
            return AccountState(action, self.state if self.state in ELIGIBLE else self.previous)
        raise AccountError("invalid_state", "This transition is unavailable.")
