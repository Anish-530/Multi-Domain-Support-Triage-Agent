"""Load markdown support corpus files into structured Document objects."""

import os
from pathlib import Path
from typing import List


class Document:
    def __init__(self, content: str, path: str, company: str) -> None:
        self.content = content
        self.path = path
        self.company = company
        self.filename = os.path.basename(path)

    def __repr__(self) -> str:
        return (
            f"Document(filename={self.filename!r}, "
            f"company={self.company!r}, "
            f"path={self.path!r})"
        )


def _load_company_documents(company_root: Path, company_name: str) -> List[Document]:
    documents: List[Document] = []
    for current_root, _, filenames in os.walk(company_root):
        for filename in filenames:
            if not filename.lower().endswith(".md"):
                continue
            file_path = Path(current_root) / filename
            content = file_path.read_text(encoding="utf-8", errors="replace")
            document = Document(content=content, path=str(file_path), company=company_name)
            documents.append(document)
    return documents


def load_all_documents(repo_root: Path) -> List[Document]:
    data_root = repo_root / "data"
    company_folders = ["hackerrank", "claude", "visa"]
    all_documents: List[Document] = []
    for company_name in company_folders:
        company_root = data_root / company_name
        if not company_root.exists():
            continue
        all_documents.extend(_load_company_documents(company_root, company_name))
    return all_documents
