class CareerPilotException(Exception):
    """Base exception for all CareerPilot AI domain errors."""
    pass


class LLMProviderError(CareerPilotException):
    """Raised when an LLM provider fails to generate or returns invalid data."""
    pass


class TruthGuardViolationError(CareerPilotException):
    """Raised when an ungrounded or unsupported claim attempts to bypass verification."""
    pass


class ParserError(CareerPilotException):
    """Raised when parsing a resume or job description fails."""
    pass


class DatabaseError(CareerPilotException):
    """Raised when a database operation fails."""
    pass


class RAGRetrievalError(CareerPilotException):
    """Raised when evidence retrieval from ChromaDB fails."""
    pass
