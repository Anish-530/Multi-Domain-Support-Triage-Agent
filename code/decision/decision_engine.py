"""Decision engine that chooses reply vs escalation and product area."""

from typing import Dict
from typing import List
from typing import Protocol

from corpus.loader import Document


class TicketLike(Protocol):
    issue: str
    subject: str
    company: str


_AREA_PRIORITY = {
    "payments": 1,
    "authentication": 2,
    "assessments": 3,
    "api": 4,
    "interviews": 5,
    "account": 6,
}

_KEYWORD_AREA_PAIRS = (
    (("payment", "refund", "billing"), "payments"),
    (("login", "access", "password"), "authentication"),
    (("test", "challenge"), "assessments"),
    (("api",), "api"),
    (("interview",), "interviews"),
    (("account",), "account"),
)


def infer_product_area(
    ticket: TicketLike,
    retrieved_docs: List[Document],
) -> str:
    """Map keywords from ticket text and top doc path to a single product_area."""
    parts = [ticket.issue or "", ticket.subject or ""]
    if retrieved_docs:
        parts.append(retrieved_docs[0].path or "")
    combined = " ".join(parts).lower()

    matched_areas: List[str] = []
    for keywords, area in _KEYWORD_AREA_PAIRS:
        if any(kw in combined for kw in keywords):
            matched_areas.append(area)

    if matched_areas:
        return min(matched_areas, key=lambda a: _AREA_PRIORITY.get(a, 99))

    return "general"


def decide_action(
    ticket: TicketLike,
    request_type: str,
    risk_flags: Dict[str, bool],
    retrieved_docs: List[Document],
    confidence: float,
) -> Dict[str, str]:
    if risk_flags["is_malicious"]:
        return {"status": "escalated", "product_area": "general"}

    if not retrieved_docs:
        return {"status": "escalated", "product_area": "general"}

    if risk_flags["is_sensitive"] and confidence < 0.6:
        return {"status": "escalated", "product_area": "general"}

    if confidence < 0.35:
        return {"status": "escalated", "product_area": "general"}

    if confidence < 0.5:
        if request_type == "bug":
            return {
                "status": "replied",
                "product_area": infer_product_area(ticket, retrieved_docs),
            }
        return {"status": "escalated", "product_area": "general"}

    return {
        "status": "replied",
        "product_area": infer_product_area(ticket, retrieved_docs),
    }
