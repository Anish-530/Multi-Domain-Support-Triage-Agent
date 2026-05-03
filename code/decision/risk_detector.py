"""Rule-based risk detector for sensitive and malicious ticket content."""

from typing import Dict
from typing import Protocol


class TicketLike(Protocol):
    issue: str
    subject: str


def detect_risk(ticket: TicketLike) -> Dict[str, bool]:
    combined_text = f"{ticket.issue} {ticket.subject}"
    text = combined_text.lower()

    account_sensitive = ["account", "login", "access", "password"]
    payment_sensitive = ["payment", "refund", "billing", "charge"]
    fraud_sensitive = ["fraud", "scam", "unauthorized"]
    sensitive_keywords = account_sensitive + payment_sensitive + fraud_sensitive

    malicious_keywords = ["delete all", "hack system", "exploit", "bypass"]

    is_sensitive = any(keyword in text for keyword in sensitive_keywords)
    is_malicious = any(keyword in text for keyword in malicious_keywords)
    needs_escalation = is_sensitive or is_malicious

    return {
        "is_sensitive": is_sensitive,
        "is_malicious": is_malicious,
        "needs_escalation": needs_escalation,
    }
