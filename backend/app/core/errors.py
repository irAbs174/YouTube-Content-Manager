"""Domain exceptions mapped to HTTP responses by the API layer."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected business-rule failures."""

    status_code = 400
    default_message = "Request could not be processed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class NotFoundError(DomainError):
    status_code = 404
    default_message = "Resource not found"


class ValidationError(DomainError):
    status_code = 400
    default_message = "Invalid input"


class FFmpegUnavailableError(DomainError):
    status_code = 503
    default_message = "FFmpeg is not available on this machine"
