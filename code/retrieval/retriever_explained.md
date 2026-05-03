# retriever.py — Explained

This file defines the `Retriever` class — the single object that `main.py` uses to find relevant documentation for every ticket. It wraps the FAISS index, the embedding model, the document metadata, and the structure map into one reusable object, and exposes a single `retrieve()` method that does everything needed to get the right documents for a query.

---

## What this file does overall

It is a thin orchestration layer. The actual FAISS search logic lives in `indexer.py`; the `Retriever` class here coordinates that logic by calling `search_with_filters()` first, then passing the results through `rerank_documents()`, and finally returning both the ranked documents and their original similarity scores.

---

## Imports

- **typing (Any, Dict, List, Tuple)** — used to annotate types across the class. `Any` is used for the FAISS index because FAISS index objects do not have a clean Python type annotation.
- **SentenceTransformer** — the type of the embedding model, imported for clarity in the constructor signature.
- **Document (from corpus.loader)** — the document type that flows through the entire retrieval pipeline.
- **rerank_documents, search_with_filters (from corpus.indexer)** — the two core search functions this class orchestrates.

---

## The Retriever class

**Why a class rather than a function:** The Retriever holds four pieces of state — the FAISS index, the document metadata, the embedding model, and the structure map. These are expensive to create (the model takes seconds to load, the index takes time to build). By storing them as instance variables on a class, `main.py` creates the Retriever once and reuses it for every ticket without rebuilding anything.

**If this were replaced with standalone functions:** Each ticket would need the index, metadata, model, and structure passed in as arguments every time — verbose, error-prone, and easy to get out of sync.

---

## `__init__()` — the constructor

This stores all four pieces of retrieval infrastructure as instance variables:

- **self.index** — the FAISS index that holds all document vectors. This is what gets searched.
- **self.metadata** — the list of Document objects aligned with the FAISS index. FAISS only knows about vector positions; this list maps position back to the actual document.
- **self.model** — the sentence transformer model used to convert a query string into a vector at search time.
- **self.structure** — the hierarchical company/category map from `structure.py`. Stored here for potential future use in navigation-style retrieval.

---

## retrieve()

This is the only public method. It takes a query string and an optional company filter, and returns a list of documents plus a list of their similarity scores.

**Step 1 — Search with filters:** It calls `search_with_filters()` from `indexer.py`, passing the query, the FAISS index, the document metadata, the model, the company filter, and a request for the top 5 results. This function handles fetching a larger candidate pool of 20, applying the company filter, and falling back to unfiltered results if the filter leaves too few documents.

The result is a list of `(Document, score)` pairs ordered by FAISS similarity.

**Step 2 — Separate documents from scores:** The list of pairs is unpacked into two separate things: a plain list of documents (for reranking) and a dictionary mapping each document's memory identity to its score (for reconstructing scores after reranking changes the order).

**Why memory identity (`id()`):** After reranking shuffles the document order, we need to look up the original FAISS score for each document. Since document objects are not hashable by content, using Python's `id()` — the object's memory address — as a key is the correct and safe way to do this.

**Step 3 — Rerank:** It calls `rerank_documents()` from `indexer.py`, which promotes documents whose file paths contain query keywords. The order of documents may change after this step.

**Step 4 — Reconstruct scores:** After reranking, it rebuilds the score list in the new document order by looking up each document's original FAISS score from the dictionary built in Step 2.

**Step 5 — Return:** Returns the top 5 reranked documents and their aligned FAISS scores. The scores are what `compute_confidence()` in `decision/confidence.py` uses to judge how good the retrieval evidence is.

---

## What breaks if this file is removed

`main.py` imports `Retriever` and creates one instance before processing any tickets. Without this file, the import fails and the system crashes before a single ticket is processed. Every downstream step — confidence, decision, response, justification — depends on what this file returns.
