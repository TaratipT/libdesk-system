from typing import List, Dict, Any, Optional
from app.rag.vector_store import VectorStore

_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store

def retrieve_regulations(
    query: str, 
    top_k: int = 3, 
    min_score: float = 0.18
) -> Dict[str, Any]:
    store = get_vector_store()
    results = store.search(query=query, top_k=top_k, min_score=min_score)
    citations = [doc["citation"] for doc in results]
    context_text = store.format_for_prompt(results)

    return {
        "query": query,
        "results": results,
        "citations": citations,
        "context": context_text
    }

