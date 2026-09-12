import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from careerpilot.core.constants import LLMProviderType, AppEnvironmentMode


def _get_secret_or_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve secret from environment variable or Streamlit secrets if available."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def _determine_mode() -> AppEnvironmentMode:
    mode_raw = _get_secret_or_env("CAREERPILOT_MODE")
    if mode_raw:
        try:
            return AppEnvironmentMode(str(mode_raw).strip().upper())
        except Exception:
            pass
    # If running on Streamlit Cloud (indicated by /mount/src or typical Streamlit cloud environment)
    if Path("/mount/src").exists() or os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("STREAMLIT_SERVER_PORT"):
        return AppEnvironmentMode.DEMO
    if (Path(__file__).resolve().parent.parent.parent / "data" / "candidate" / "profile.yaml").exists():
        return AppEnvironmentMode.LOCAL_PRIVATE
    return AppEnvironmentMode.DEMO


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "CareerPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Environment Mode: DEMO (synthetic public) vs LOCAL_PRIVATE (local verified)
    CAREERPILOT_MODE: AppEnvironmentMode = Field(default_factory=_determine_mode)

    # Base Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data")
    
    # Specific Data Source Paths
    CANDIDATE_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "candidate")
    DEMO_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "demo")
    PRIVATE_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "private")
    KNOWLEDGE_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "knowledge")
    EVALUATION_JOBS_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "jobs" / "evaluation")
    SAMPLE_DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "sample")
    
    # Artifact Output Paths
    OUTPUT_RESUMES_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "generated" / "resumes")
    OUTPUT_INTERVIEW_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "generated" / "interview_prep")
    OUTPUT_MOCK_SESSIONS_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "generated" / "interview_sessions")
    UPLOADS_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data" / "uploads")

    # LLM Settings
    LLM_PROVIDER: LLMProviderType = LLMProviderType.GEMINI
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: _get_secret_or_env("GEMINI_API_KEY"))
    GEMINI_MODEL: str = "gemini-3.6-flash"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Embedding & Vector Database
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default_factory=lambda: str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db")
    )

    # SQLite Database
    SQLITE_DB_PATH: str = Field(
        default_factory=lambda: str(Path(__file__).resolve().parent.parent.parent / "data" / "careerpilot.db")
    )

    # Scoring Weights (Configurable)
    WEIGHT_MUST_HAVE: float = 0.35
    WEIGHT_EXPERIENCE: float = 0.20
    WEIGHT_ROLE_ALIGNMENT: float = 0.15
    WEIGHT_GENAI_ALIGNMENT: float = 0.10
    WEIGHT_DATA_ENG_ALIGNMENT: float = 0.10
    WEIGHT_CLOUD_ALIGNMENT: float = 0.05
    WEIGHT_PREFERENCES: float = 0.05

    # Must-Have Penalty Config
    MUST_HAVE_PENALTY_PER_GAP: float = 12.0  # Points deducted per missing must-have

    # Decision Engine Thresholds
    DECISION_APPLY_THRESHOLD: float = 75.0
    DECISION_REVIEW_THRESHOLD: float = 55.0

    # ATS Scoring Component Weights (Configurable)
    ATS_WEIGHT_KEYWORD_COVERAGE: float = 0.25
    ATS_WEIGHT_SKILL_TAXONOMY: float = 0.20
    ATS_WEIGHT_SEMANTIC_ALIGNMENT: float = 0.15
    ATS_WEIGHT_EXPERIENCE_ALIGNMENT: float = 0.15
    ATS_WEIGHT_STRUCTURE: float = 0.10
    ATS_WEIGHT_FORMATTING: float = 0.10
    ATS_WEIGHT_READABILITY: float = 0.05

    # File Upload Security Limits
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_UPLOAD_EXTENSIONS: tuple = (".pdf", ".txt")

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_demo_mode(self) -> bool:
        return self.CAREERPILOT_MODE == AppEnvironmentMode.DEMO

    @property
    def active_candidate_dir(self) -> Path:
        """Returns demo directory in DEMO mode, else candidate/private directory."""
        if self.is_demo_mode:
            return self.DEMO_DATA_DIR
        if self.PRIVATE_DATA_DIR.exists() and (self.PRIVATE_DATA_DIR / "profile.yaml").exists():
            return self.PRIVATE_DATA_DIR
        return self.CANDIDATE_DATA_DIR

    @property
    def is_hosted_private_mode(self) -> bool:
        return self.CAREERPILOT_MODE == AppEnvironmentMode.HOSTED_PRIVATE

    @property
    def is_local_private_mode(self) -> bool:
        return self.CAREERPILOT_MODE == AppEnvironmentMode.LOCAL_PRIVATE

    @property
    def active_candidate_id(self) -> str:
        """Returns candidate ID string matching current mode."""
        return "trupti_kularkar"

    def validate_deployment_persistence(self) -> Tuple[bool, str]:
        """
        Validates persistent database & storage configuration for HOSTED_PRIVATE mode.
        Guarantees that production deployments do not silently lose candidate data on restart.
        """
        if self.is_hosted_private_mode:
            db_url = os.environ.get("DATABASE_URL")
            persist_vol = os.environ.get("PERSISTENT_VOLUME_PATH")
            allow_ephemeral = os.environ.get("ALLOW_EPHEMERAL_HOSTED_STORAGE")
            if not db_url and not persist_vol and not allow_ephemeral:
                return False, (
                    "HOSTED_PRIVATE mode requires persistent storage configuration. "
                    "Please configure DATABASE_URL (e.g. PostgreSQL) or PERSISTENT_VOLUME_PATH."
                )
        return True, "Storage configuration validated."

    @property
    def masked_gemini_key(self) -> Optional[str]:
        """Returns masked API key for safe diagnostics display."""
        if not self.GEMINI_API_KEY:
            return None
        if len(self.GEMINI_API_KEY) <= 8:
            return "****"
        return f"{self.GEMINI_API_KEY[:4]}...{self.GEMINI_API_KEY[-4:]}"

    def ensure_directories(self) -> None:
        """Ensure necessary runtime directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CANDIDATE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.PRIVATE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.KNOWLEDGE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.EVALUATION_JOBS_DIR.mkdir(parents=True, exist_ok=True)
        self.SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_RESUMES_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_INTERVIEW_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_MOCK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
