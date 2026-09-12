import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResumeArtifact(BaseModel):
    """
    Represents a generated physical or in-memory resume file artifact (PDF, DOCX, Markdown).
    Decouples generated file/IO concerns from the core TailoredResume domain model.
    Implements os.PathLike so it can be passed directly to open() or Path() if needed.
    """
    artifact_type: str  # "pdf", "docx", "markdown", "json"
    file_name: str
    file_path: Optional[str] = None
    content_type: str
    file_bytes: Optional[bytes] = None
    created_at: str = Field(default_factory=utc_iso)
    resume_id: str
    is_valid: bool = True
    validation_message: Optional[str] = None

    def __fspath__(self) -> str:
        return self.file_path or self.file_name

    def __str__(self) -> str:
        return self.file_path or self.file_name

    def exists(self) -> bool:
        """Checks if the underlying file path exists on disk."""
        if self.file_path:
            return Path(self.file_path).exists()
        return self.file_bytes is not None

    def stat(self) -> Any:
        """Returns os.stat_result for the underlying file path."""
        if self.file_path:
            return Path(self.file_path).stat()
        raise FileNotFoundError(f"No file path associated with artifact '{self.file_name}'")

    def get_bytes(self) -> bytes:
        """Retrieves artifact binary bytes from memory or disk."""
        if self.file_bytes is not None:
            return self.file_bytes
        if self.file_path and Path(self.file_path).exists():
            with open(self.file_path, "rb") as f:
                return f.read()
        return b""

    def read_bytes(self) -> bytes:
        """Convenience method matching Path.read_bytes()."""
        return self.get_bytes()

    def read_text(self, encoding: str = "utf-8") -> str:
        """Convenience method matching Path.read_text()."""
        return self.get_bytes().decode(encoding, errors="replace")


class ResumeArtifactBundle(BaseModel):
    """
    Container bundle of all exported file artifacts associated with a tailored resume run.
    """
    resume_id: str
    pdf: Optional[ResumeArtifact] = None
    docx: Optional[ResumeArtifact] = None
    markdown: Optional[ResumeArtifact] = None
