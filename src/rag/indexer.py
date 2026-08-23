"""Index and scoring engine for Knowledge Base chunks."""
import math
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from src.models import DocumentChunk, DocumentMetadata
from src.rag.parser import DocumentParser
from src.rag.chunker import MarkdownChunker
from src.config import KNOWLEDGE_BASE_DIR


def tokenize(text: str) -> List[str]:
    """Tokenizes text into normalized alphanumeric words."""
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    return [w for w in cleaned.split() if len(w) > 1]


class DocumentIndex:
    """In-memory BM25 + Metadata aware search index."""

    def __init__(self, kb_dir: Path = KNOWLEDGE_BASE_DIR):
        self.kb_dir = kb_dir
        self.chunks: List[DocumentChunk] = []
        self.doc_frequencies: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.total_chunks: int = 0
        self.k1: float = 1.5
        self.b: float = 0.75
        self.build_index()

    def build_index(self):
        """Loads and indexes all markdown documents from knowledge-base directory."""
        self.chunks = []
        md_files = sorted(list(self.kb_dir.glob("*.md")))
        
        total_tokens = 0
        for file_path in md_files:
            metadata, body = DocumentParser.parse_file(file_path)
            doc_chunks = MarkdownChunker.chunk_document(metadata, body)
            self.chunks.extend(doc_chunks)

        self.total_chunks = len(self.chunks)
        if self.total_chunks == 0:
            return

        # Calculate document frequencies
        df: Dict[str, int] = {}
        for chunk in self.chunks:
            full_text = f"{chunk.metadata.title} {chunk.heading} {chunk.content}"
            tokens = set(tokenize(full_text))
            total_tokens += len(tokenize(full_text))
            for token in tokens:
                df[token] = df.get(token, 0) + 1

        self.doc_frequencies = df
        self.avg_doc_len = total_tokens / float(self.total_chunks) if self.total_chunks else 1.0

    def calculate_bm25_score(self, query_tokens: List[str], chunk: DocumentChunk) -> float:
        """Calculates standard BM25 score for a chunk with heading and metadata weighting."""
        chunk_text = chunk.content
        heading_text = f"{chunk.metadata.title} {chunk.heading} {chunk.subheading or ''}"
        
        chunk_tokens = tokenize(chunk_text)
        heading_tokens = tokenize(heading_text)
        doc_len = len(chunk_tokens) + len(heading_tokens)

        score = 0.0
        for token in query_tokens:
            # Term frequencies
            tf_body = chunk_tokens.count(token)
            tf_heading = heading_tokens.count(token) * 3.0  # boost heading matches
            tf = tf_body + tf_heading

            if tf == 0:
                continue

            n_q = self.doc_frequencies.get(token, 0)
            idf = math.log((self.total_chunks - n_q + 0.5) / (n_q + 0.5) + 1.0)
            if idf < 0:
                idf = 0.1

            term_score = idf * ((tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))))
            score += term_score

        # Multipliers based on document authority and status
        if chunk.metadata.status == "superseded":
            score *= 0.35  # Deprecate superseded documents
        elif chunk.metadata.status == "draft" or chunk.metadata.policy_authority == "none" or not chunk.metadata.customer_answering:
            score *= 0.20  # Deprecate internal draft notes for customer policy answering
        elif chunk.metadata.status == "active" and chunk.metadata.policy_authority == "official":
            score *= 1.25  # Boost active official policies

        # Boost specific exact phrase matches in heading
        query_str = " ".join(query_tokens)
        if query_str in heading_text.lower():
            score += 4.0

        return score
