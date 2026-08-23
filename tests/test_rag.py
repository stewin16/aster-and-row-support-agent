"""Unit tests for RAG parser, chunker, indexer, and retriever."""
from src.rag.parser import DocumentParser
from src.rag.chunker import MarkdownChunker
from src.rag.indexer import DocumentIndex
from src.rag.retriever import KnowledgeRetriever
from src.config import KNOWLEDGE_BASE_DIR


def test_parser_frontmatter():
    file_path = KNOWLEDGE_BASE_DIR / "01-returns-policy-current.md"
    metadata, body = DocumentParser.parse_file(file_path)
    assert metadata.document_id == "RET-2026-01"
    assert metadata.status == "active"
    assert metadata.policy_authority == "official"
    assert metadata.customer_answering is True
    assert "Returns Policy" in body


def test_superseded_precedence():
    index = DocumentIndex(KNOWLEDGE_BASE_DIR)
    retriever = KnowledgeRetriever(index)
    chunks, _ = retriever.retrieve("How long do I have to return an item on the standard plan?")
    assert len(chunks) > 0
    # Top chunk should be from current return policy, NOT legacy
    assert chunks[0].filename == "01-returns-policy-current.md"
    assert chunks[0].metadata.status == "active"


def test_conflict_detection():
    retriever = KnowledgeRetriever()
    chunks, conflicts = retriever.retrieve("Can I put the entire Breeze Tumbler in the dishwasher?")
    assert len(conflicts) > 0
    assert "Conflict detected on Breeze Tumbler cleaning" in conflicts[0]
