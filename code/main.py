"""Final end-to-end ticket triage runner that writes support_tickets/output.csv."""

import csv
import re
from pathlib import Path
from typing import Dict, List

from corpus.loader import load_all_documents
from corpus.structure import build_structure
from corpus.indexer import build_faiss_index, load_embedding_model
from retrieval.retriever import Retriever
from classification.classifier import classify_request_type
from decision.risk_detector import detect_risk
from decision.confidence import compute_confidence
from decision.decision_engine import decide_action
from generation.responder import generate_response
from generation.justification import generate_justification
from output.writer import write_output


class Ticket:
    def __init__(self, issue: str, subject: str, company: str) -> None:
        self.issue = (issue or "").strip()
        self.subject = (subject or "").strip()
        self.company = (company or "").strip().lower()


def prioritize_issue_intent(issue: str) -> str:
    parts = [part.strip() for part in re.split(r"\band\b|\balso\b", issue, flags=re.IGNORECASE) if part.strip()]
    if not parts:
        return issue
    critical_keywords = [
        "fraud",
        "scam",
        "unauthorized",
        "password",
        "access",
        "login",
        "payment",
        "refund",
        "charge",
        "bug",
        "failed",
        "error",
        "not working",
    ]
    for part in parts:
        lower_part = part.lower()
        if any(keyword in lower_part for keyword in critical_keywords):
            return part
    return parts[0]


def load_tickets(csv_path: Path) -> List[Ticket]:
    tickets: List[Ticket] = []
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            issue = row.get("Issue", "")
            subject = row.get("Subject", "")
            company = row.get("Company", "")
            ticket = Ticket(issue=issue, subject=subject, company=company)
            tickets.append(ticket)
    return tickets


def verify_output(output_path: Path, expected_rows: int) -> None:
    required_columns = [
        "issue",
        "subject",
        "company",
        "response",
        "product_area",
        "status",
        "request_type",
        "justification",
    ]
    valid_status = {"replied", "escalated"}
    valid_request_type = {"product_issue", "feature_request", "bug", "invalid"}
    with output_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = reader.fieldnames or []
        rows = list(reader)

    # Raise error when output schema order/columns does not match expectation.
    if columns != required_columns:
        raise ValueError(f"Invalid output columns: {columns}")

    # Raise error when output row count differs from input row count.
    if len(rows) != expected_rows:
        raise ValueError(f"Row count mismatch: expected {expected_rows}, got {len(rows)}")

    # Validate each row for missing fields and allowed enumerated values.
    for index, row in enumerate(rows, start=1):
        for column in required_columns:
            if column not in row:
                raise ValueError(f"Missing column {column} in row {index}")
        if row["status"] not in valid_status:
            raise ValueError(f"Invalid status '{row['status']}' in row {index}")
        if row["request_type"] not in valid_request_type:
            raise ValueError(f"Invalid request_type '{row['request_type']}' in row {index}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv_path = repo_root / "support_tickets" / "support_tickets.csv"
    output_csv_path = repo_root / "support_tickets" / "output.csv"

    documents = load_all_documents(repo_root=repo_root)
    structure = build_structure(documents)
    model = load_embedding_model("sentence-transformers/all-MiniLM-L6-v2")
    index, _, metadata = build_faiss_index(documents=documents, model=model)
    retriever = Retriever(index=index, metadata=metadata, model=model, structure=structure)

    tickets = load_tickets(input_csv_path)
    output_rows: List[Dict[str, str]] = []
    reply_count = 0
    escalation_count = 0

    for ticket in tickets:
        try:
            if not ticket.issue:
                edge_row = {
                    "issue": ticket.issue,
                    "subject": ticket.subject,
                    "company": ticket.company,
                    "response": "Insufficient information. Escalating.",
                    "product_area": "general",
                    "status": "escalated",
                    "request_type": "invalid",
                    "justification": "Issue text was empty, so escalation was required.",
                }
                output_rows.append(edge_row)
                escalation_count += 1
                continue

            prioritized_issue = prioritize_issue_intent(ticket.issue)
            prioritized_ticket = Ticket(
                issue=prioritized_issue,
                subject=ticket.subject,
                company=ticket.company,
            )
            request_type = classify_request_type(prioritized_ticket)
            risk_flags = detect_risk(prioritized_ticket)

            company_filter = None if ticket.company in {"", "none"} else ticket.company
            retrieved_docs, scores = retriever.retrieve(query=prioritized_issue, company=company_filter)
            confidence = compute_confidence(scores)

            decision = decide_action(
                ticket=prioritized_ticket,
                request_type=request_type,
                risk_flags=risk_flags,
                retrieved_docs=retrieved_docs,
                confidence=confidence,
            )

            response = generate_response(
                ticket=ticket,
                retrieved_docs=retrieved_docs,
                status=decision["status"],
            )
            justification = generate_justification(
                ticket=ticket,
                request_type=request_type,
                risk_flags=risk_flags,
                status=decision["status"],
                retrieved_docs=retrieved_docs,
                confidence=confidence,
            )

            output_row = {
                "issue": ticket.issue,
                "subject": ticket.subject,
                "company": ticket.company,
                "response": response,
                "product_area": decision["product_area"],
                "status": decision["status"],
                "request_type": request_type,
                "justification": justification,
            }
            output_rows.append(output_row)

            if decision["status"] == "replied":
                reply_count += 1
            else:
                escalation_count += 1
        except Exception as error:
            # Fallback safe row for any unexpected per-ticket processing failure.
            fallback_row = {
                "issue": ticket.issue,
                "subject": ticket.subject,
                "company": ticket.company,
                "response": "Your issue requires further review by our support team.",
                "product_area": "general",
                "status": "escalated",
                "request_type": "invalid",
                "justification": f"Ticket processing failed safely: {str(error)}",
            }

            # Append safe fallback row so no ticket is skipped.
            output_rows.append(fallback_row)
            escalation_count += 1

    write_output(rows=output_rows, output_path=output_csv_path)
    verify_output(output_path=output_csv_path, expected_rows=len(tickets))

    print(f"total tickets processed: {len(tickets)}")
    print(f"number of replies: {reply_count}")
    print(f"number of escalations: {escalation_count}")
    print(f"output written to: {output_csv_path}")


if __name__ == "__main__":
    main()
