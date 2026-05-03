"""CSV output writer for final support triage predictions."""

import csv
from pathlib import Path
from typing import Dict, List


def write_output(rows: List[Dict[str, str]], output_path: Path) -> None:
    fieldnames = [
        "issue",
        "subject",
        "company",
        "response",
        "product_area",
        "status",
        "request_type",
        "justification",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            normalized_row = {
                "issue": str(row.get("issue", "")),
                "subject": str(row.get("subject", "")),
                "company": str(row.get("company", "")),
                "response": str(row.get("response", "")),
                "product_area": str(row.get("product_area", "")),
                "status": str(row.get("status", "")).lower(),
                "request_type": str(row.get("request_type", "")).lower(),
                "justification": str(row.get("justification", "")),
            }
            writer.writerow(normalized_row)
