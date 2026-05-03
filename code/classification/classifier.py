"""Rule-based request type classifier for support tickets."""

import re
from typing import Protocol


class TicketLike(Protocol):
    issue: str
    subject: str


def classify_request_type(ticket: TicketLike) -> str:
    combined_text = f"{ticket.issue} {ticket.subject}"
    text = combined_text.lower()

    if "delete system" in text:
        return "invalid"
    if re.search(r"\b(hack|exploit|bypass)\b", text):
        return "invalid"

    feature_keywords = ["add", "feature", "request", "improve"]
    if any(keyword in text for keyword in feature_keywords):
        return "feature_request"

    bug_keywords = ["error", "not working", "failed", "bug"]
    if any(keyword in text for keyword in bug_keywords):
        return "bug"

    return "product_issue"
