"""Markdown and YAML front matter parser for knowledge base documents."""
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml
from src.models import DocumentMetadata


class DocumentParser:
    """Parses markdown files with YAML front matter."""

    FRONT_MATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    @classmethod
    def parse_file(cls, file_path: Path) -> Tuple[DocumentMetadata, str]:
        """Parses a markdown file into DocumentMetadata and raw markdown body."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        match = cls.FRONT_MATTER_REGEX.match(content)
        if match:
            front_matter_str = match.group(1)
            body = content[match.end():]
            try:
                front_matter_dict = yaml.safe_load(front_matter_str) or {}
            except Exception:
                front_matter_dict = {}
        else:
            front_matter_dict = {}
            body = content

        metadata = DocumentMetadata(
            document_id=str(front_matter_dict.get("document_id", file_path.stem)),
            title=str(front_matter_dict.get("title", file_path.stem)),
            status=front_matter_dict.get("status", "active"),
            effective_date=str(front_matter_dict.get("effective_date")) if front_matter_dict.get("effective_date") else None,
            superseded_date=str(front_matter_dict.get("superseded_date")) if front_matter_dict.get("superseded_date") else None,
            last_reviewed=str(front_matter_dict.get("last_reviewed")) if front_matter_dict.get("last_reviewed") else None,
            audience=front_matter_dict.get("audience", "customer"),
            policy_authority=front_matter_dict.get("policy_authority", "official"),
            supersedes=str(front_matter_dict.get("supersedes")) if front_matter_dict.get("supersedes") else None,
            superseded_by=str(front_matter_dict.get("superseded_by")) if front_matter_dict.get("superseded_by") else None,
            customer_answering=bool(front_matter_dict.get("customer_answering", True)),
            filename=file_path.name,
        )

        return metadata, body
