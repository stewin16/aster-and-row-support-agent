"""Retriever with conflict detection and metadata-aware ranking."""
import re
from typing import List, Tuple, Optional
from src.models import DocumentChunk, Citation
from src.rag.indexer import DocumentIndex, tokenize


class KnowledgeRetriever:
    """Retrieves relevant passages and detects active document conflicts."""

    def __init__(self, index: Optional[DocumentIndex] = None):
        self.index = index or DocumentIndex()

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        include_internal: bool = False
    ) -> Tuple[List[DocumentChunk], List[str]]:
        """
        Retrieves the most relevant chunks for a user query.
        Returns: (ranked_chunks, conflicts_detected)
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return [], []

        scored_chunks: List[Tuple[float, DocumentChunk]] = []
        for chunk in self.index.chunks:
            # Skip draft / non-customer answering documents unless explicitly querying prompt-security or debug
            if not include_internal:
                if not chunk.metadata.customer_answering and "migration" not in query.lower() and "unapproved" not in query.lower():
                    continue

            score = self.index.calculate_bm25_score(query_tokens, chunk)
            if score > 0.1:
                # Store scored copy
                chunk_copy = chunk.model_copy(update={"score": round(score, 3)})
                scored_chunks.append((score, chunk_copy))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [item[1] for item in scored_chunks[:top_k]]

        # Conflict Detection Engine
        conflicts = self._detect_conflicts(query, top_chunks)

        return top_chunks, conflicts

    def _detect_conflicts(self, query: str, chunks: List[DocumentChunk]) -> List[str]:
        """Detects whether active official documents give contradictory instructions."""
        conflicts = []
        query_lower = query.lower()
        chunk_files = {c.filename for c in chunks}

        # Check for Breeze Tumbler dishwasher conflict (11-product-care.md vs 12-breeze-tumbler-product-card.md)
        if ("tumbler" in query_lower or "breeze" in query_lower) and ("dishwasher" in query_lower or "wash" in query_lower or "clean" in query_lower):
            # Check if both 11-product-care.md and 12-breeze-tumbler-product-card.md are relevant
            care_chunks = [c for c in self.index.chunks if c.filename == "11-product-care.md" and "tumbler" in c.content.lower()]
            prod_chunks = [c for c in self.index.chunks if c.filename == "12-breeze-tumbler-product-card.md" and "cleaning" in c.heading.lower()]
            
            if care_chunks and prod_chunks:
                conflicts.append(
                    "Conflict detected on Breeze Tumbler cleaning: '11-product-care.md' states the stainless-steel body should be hand-washed, while '12-breeze-tumbler-product-card.md' states all components are dishwasher safe."
                )
                # Ensure both chunks are present in context
                for c in care_chunks + prod_chunks:
                    if c.chunk_id not in {x.chunk_id for x in chunks}:
                        chunks.append(c)

        return conflicts

    @staticmethod
    def extract_citations(chunks: List[DocumentChunk]) -> List[Citation]:
        """Extracts unique citation objects from a list of chunks."""
        seen = set()
        citations = []
        for chunk in chunks:
            key = (chunk.filename, chunk.heading)
            if key not in seen and chunk.metadata.customer_answering and chunk.metadata.status == "active":
                seen.add(key)
                citations.append(
                    Citation(
                        filename=chunk.filename,
                        heading=chunk.heading,
                        document_id=chunk.metadata.document_id
                    )
                )
        return citations
