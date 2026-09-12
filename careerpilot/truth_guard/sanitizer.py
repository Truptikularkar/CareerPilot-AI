import re
from typing import List, Tuple
from careerpilot.core.logging import get_logger


logger = get_logger(__name__)


class TextSanitizer:
    """
    Sanitizes draft resume text by correcting phrasing to adhere to verified ground truth.
    """

    REPLACEMENTS = [
        (re.compile(r"\baws\s+production\s+experience\b", re.IGNORECASE), "GCP production experience with transferable AWS cloud knowledge"),
        (re.compile(r"\bclient\s+rag\s+platform\b", re.IGNORECASE), "local RAG & hybrid retrieval sandbox"),
        (re.compile(r"\b(\d+)\s*years\s+of\s+experience\b", re.IGNORECASE), "1.9+ years of experience"),
    ]

    @classmethod
    def sanitize_draft_text(cls, text: str) -> str:
        """Applies truth-preserving corrections to text."""
        sanitized = text
        for pattern, replacement in cls.REPLACEMENTS:
            if pattern.search(sanitized):
                sanitized = pattern.sub(replacement, sanitized)
                logger.info("Sanitized unsupported phrase: %s -> %s", pattern.pattern, replacement)
        return sanitized
