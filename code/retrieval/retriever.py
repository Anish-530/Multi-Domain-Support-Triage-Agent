"""Retriever that combines semantic FAISS search with structure-aware reranking."""

# Import Any for flexible typing of FAISS index object references.
from typing import Any
# Import Dict for typing the structure mapping passed into Retriever.
from typing import Dict
# Import List for typing returned collections of Document objects.
from typing import List
# Import Tuple for explicit multi-value return typing.
from typing import Tuple

# Import SentenceTransformer type for model argument clarity.
from sentence_transformers import SentenceTransformer

# Import Document metadata type used across retrieval pipeline.
from corpus.loader import Document
# Import filtered search and reranking helpers from indexer module.
from corpus.indexer import rerank_documents, search_with_filters


# Define a retriever class that orchestrates semantic + structure-aware retrieval.
class Retriever:
    # Initialize retriever with ready-to-use index, metadata, model, and structure map.
    def __init__(
        self,
        index: Any,
        metadata: List[Document],
        model: SentenceTransformer,
        structure: Dict[str, Dict[str, List[Document]]],
    ) -> None:
        # Store FAISS index for semantic nearest-neighbor search.
        self.index = index
        # Store metadata so FAISS vector rows can map back to documents.
        self.metadata = metadata
        # Store embedding model used for query vectorization at search time.
        self.model = model
        # Store hierarchical structure for PageIndex-like navigation context.
        self.structure = structure

    # Retrieve top documents by combining company filter, FAISS search, and rerank.
    def retrieve(self, query: str, company: str) -> Tuple[List[Document], List[float]]:
        # Run semantic FAISS search with optional company filter and fallback logic.
        scored_candidates = search_with_filters(
            query=query,
            index=self.index,
            metadata=self.metadata,
            model=self.model,
            company=company,
            top_k=5,
        )
        # Split (document, score) pairs into a document list for reranking.
        candidate_documents = [document for document, _ in scored_candidates]
        # Build a lookup so reranked documents can keep their original FAISS scores.
        score_by_doc_id = {id(document): score for document, score in scored_candidates}
        # Apply lightweight structure-aware reranking using path keyword matches.
        reranked_documents = rerank_documents(query=query, documents=candidate_documents)
        # Keep only top 5 documents after reranking.
        top_documents = reranked_documents[:5]
        # Reconstruct score list in the same order as top_documents.
        top_scores = [score_by_doc_id.get(id(document), 0.0) for document in top_documents]
        # Return documents and their aligned FAISS similarity scores.
        return top_documents, top_scores
