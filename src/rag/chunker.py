"""Heading-aware markdown chunker."""
import re
from typing import List, Optional
from src.models import DocumentMetadata, DocumentChunk


class MarkdownChunker:
    """Splits markdown content into semantic chunks based on headings."""

    HEADING_REGEX = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

    @classmethod
    def chunk_document(cls, metadata: DocumentMetadata, markdown_body: str) -> List[DocumentChunk]:
        """Splits markdown into section chunks."""
        lines = markdown_body.splitlines()
        chunks: List[DocumentChunk] = []

        current_h1: str = metadata.title
        current_h2: Optional[str] = None
        current_lines: List[str] = []
        chunk_counter = 1

        def flush_chunk():
            nonlocal chunk_counter, current_lines
            content = "\n".join(current_lines).strip()
            if content:
                heading_name = current_h2 if current_h2 else current_h1
                chunk_id = f"{metadata.filename}#chunk-{chunk_counter}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        filename=metadata.filename,
                        heading=heading_name,
                        subheading=current_h2 if current_h2 else None,
                        content=content,
                        metadata=metadata,
                        score=0.0
                    )
                )
                chunk_counter += 1
            current_lines = []

        for line in lines:
            heading_match = cls.HEADING_REGEX.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                if level == 1:
                    flush_chunk()
                    current_h1 = title
                    current_h2 = None
                    current_lines.append(line)
                elif level == 2:
                    flush_chunk()
                    current_h2 = title
                    current_lines.append(line)
                else:
                    current_lines.append(line)
            else:
                current_lines.append(line)

        flush_chunk()

        # Fallback if no sections were created
        if not chunks and markdown_body.strip():
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{metadata.filename}#chunk-1",
                    filename=metadata.filename,
                    heading=metadata.title,
                    subheading=None,
                    content=markdown_body.strip(),
                    metadata=metadata,
                    score=0.0
                )
            )

        return chunks
