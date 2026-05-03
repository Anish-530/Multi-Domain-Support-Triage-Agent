"""Concise decision justification generator for support triage outputs."""

from typing import Dict
from typing import List
from typing import Protocol

from corpus.loader import Document


class TicketLike(Protocol):
    issue: str
    subject: str
    company: str


def _confidence_level_phrase(confidence: float) -> str:
    """Map numeric confidence to explicit high / moderate / low wording."""
    if confidence < 0.35:
        return "The evidence match was low confidence."
    if confidence < 0.5:
        return "The evidence match was moderate confidence."
    return "The evidence match was high confidence."


def generate_justification(
    ticket: TicketLike,
    request_type: str,
    risk_flags: Dict[str, bool],
    status: str,
    retrieved_docs: List[Document],
    confidence: float,
) -> str:
    if risk_flags["is_malicious"]:
        risk_phrase = "Malicious content indicators were detected."
    elif risk_flags["is_sensitive"]:
        risk_phrase = "Sensitive content indicators were detected."
    else:
        risk_phrase = "No sensitive or malicious content indicators were detected."

    docs_phrase = (
        "Relevant documentation was found."
        if retrieved_docs
        else "No relevant documentation was found."
    )

    conf_label = _confidence_level_phrase(confidence)

    decision_phrase = (
        "The case was escalated for further review."
        if status == "escalated"
        else "A direct response was provided."
    )

    return (
        f"This request was classified as {request_type}. "
        f"{risk_phrase} {docs_phrase} {conf_label} {decision_phrase}"
    )
