class AIServiceError(Exception):
    """Raised when the AI service experiences an error (model not loaded, inference failed, etc.)."""


class DBServiceError(Exception):
    """Raised when the DB service encounters an unexpected error."""


class TaskServiceError(Exception):
    """Generic task service error."""
