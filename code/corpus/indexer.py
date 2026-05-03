"""FAISS index builder and query search utilities for the local corpus."""

from typing import List
from typing import Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from corpus.loader import Document


def load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name)


def build_faiss_index(
    documents: List[Document],
    model: SentenceTransformer,
) -> Tuple[faiss.IndexFlatIP, np.ndarray, List[Document]]:
    texts = [document.content for document in documents]
    embeddings = model.encode(texts, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)
    embedding_dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(embeddings)
    metadata = documents
    return index, embeddings, metadata


def search_index(
    query: str,
    index: faiss.IndexFlatIP,
    metadata: List[Document],
    model: SentenceTransformer,
    top_k: int = 5,
) -> List[Document]:
    query_embedding = model.encode([query], show_progress_bar=False)
    query_embedding = np.asarray(query_embedding, dtype="float32")
    faiss.normalize_L2(query_embedding)
    _, indices = index.search(query_embedding, top_k)
    results: List[Document] = []
    for doc_index in indices[0]:
        if doc_index < 0:
            continue
        results.append(metadata[doc_index])
    return results


def rerank_documents(query: str, documents: List[Document]) -> List[Document]:
    keywords = [token.strip().lower() for token in query.split() if token.strip()]
    scored_documents = []
    for rank_index, document in enumerate(documents):
        lower_path = document.path.lower()
        keyword_match_score = sum(1 for keyword in keywords if keyword in lower_path)
        scored_documents.append((keyword_match_score, rank_index, document))
    scored_documents.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored_documents]


def search_with_filters(
    query: str,
    index: faiss.IndexFlatIP,
    metadata: List[Document],
    model: SentenceTransformer,
    company: str = None,
    top_k: int = 5,
) -> List[Tuple[Document, float]]:
    prefilter_k = 20
    query_embedding = model.encode([query], show_progress_bar=False)
    query_embedding = np.asarray(query_embedding, dtype="float32")
    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(query_embedding, prefilter_k)
    original_results: List[Tuple[Document, float]] = []
    for rank_index, doc_index in enumerate(indices[0]):
        if doc_index < 0:
            continue
        score = float(scores[0][rank_index])
        original_results.append((metadata[doc_index], score))
    if company is None:
        return original_results[:top_k]
    company = company.strip().lower()
    filtered_results = [
        (document, score)
        for document, score in original_results
        if document.company == company
    ]
    if len(filtered_results) >= top_k:
        return filtered_results[:top_k]
    return original_results[:top_k]
