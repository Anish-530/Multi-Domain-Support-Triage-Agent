"""Build a PageIndex-inspired hierarchical structure for corpus navigation."""

from typing import Dict, List
from corpus.loader import Document


def build_structure(documents: List[Document]) -> Dict[str, Dict[str, List[Document]]]:
    structured_dict: Dict[str, Dict[str, List[Document]]] = {}
    for document in documents:
        company = document.company.lower()
        normalized_path = document.path.replace("\\", "/")
        path_parts = normalized_path.split("/")
        company_index = path_parts.index(company) if company in path_parts else -1
        category = "root"
        if company_index >= 0 and company_index + 1 < len(path_parts) - 1:
            category = path_parts[company_index + 1]
        if company not in structured_dict:
            structured_dict[company] = {}
        if category not in structured_dict[company]:
            structured_dict[company][category] = []
        structured_dict[company][category].append(document)
    return structured_dict