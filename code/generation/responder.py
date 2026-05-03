"""Grounded response generator that uses only retrieved corpus snippets."""

import re
from typing import List
from typing import Protocol
from corpus.loader import Document


class TicketLike(Protocol):
    issue: str
    subject: str
    company: str


def _clean_extractive_snippet(raw: str) -> str:
    """Remove common corpus artifacts; keep text extractive (no paraphrase)."""
    text = raw[:400]

    # Drop YAML-style frontmatter fence lines.
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            continue
        lower = stripped.lower()
        if lower.startswith("title:") or lower.startswith("description:"):
            continue
        lines.append(stripped)
    joined = " ".join(lines)
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined[:200].strip()


def generate_response(ticket: TicketLike, retrieved_docs: List[Document], status: str) -> str:
    if status == "escalated":
        return "Your issue requires further review by our support team."

    if not retrieved_docs:
        return "We could not find relevant information. Your issue will be escalated."

    top_documents = retrieved_docs[:2]
    snippets: List[str] = []
    for document in top_documents:
        snippet = _clean_extractive_snippet(document.content)
        if snippet:
            snippets.append(snippet)

    response = "Based on our support documentation:\n\n"
    response += "\n\n".join(snippets)
    if len(response.strip()) < 60:
        return "Please provide more details so we can better assist you."
    return response
