"""
Custom exception hierarchy for NagiFlow.

All domain errors inherit from NagiFlowError so callers can catch a single
base class while still distinguishing specific error kinds.
"""

from http import HTTPStatus


class NagiFlowError(Exception):
    """Base exception for all NagiFlow errors."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


# ---------------------------------------------------------------------------
# Auth / Access
# ---------------------------------------------------------------------------


class AuthenticationError(NagiFlowError):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Could not validate credentials."


class PermissionDeniedError(NagiFlowError):
    status_code = HTTPStatus.FORBIDDEN
    detail = "You do not have permission to perform this action."


class TokenExpiredError(AuthenticationError):
    detail = "Token has expired."


# ---------------------------------------------------------------------------
# Resource errors
# ---------------------------------------------------------------------------


class NotFoundError(NagiFlowError):
    status_code = HTTPStatus.NOT_FOUND
    detail = "Resource not found."


class ConflictError(NagiFlowError):
    status_code = HTTPStatus.CONFLICT
    detail = "Resource already exists."


class ValidationError(NagiFlowError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    detail = "Validation error."


# ---------------------------------------------------------------------------
# Provider errors
# ---------------------------------------------------------------------------


class LLMProviderError(NagiFlowError):
    status_code = HTTPStatus.BAD_GATEWAY
    detail = "LLM provider returned an error."


class TTSProviderError(NagiFlowError):
    status_code = HTTPStatus.BAD_GATEWAY
    detail = "TTS provider returned an error."


class EmbeddingProviderError(NagiFlowError):
    status_code = HTTPStatus.BAD_GATEWAY
    detail = "Embedding provider returned an error."


# ---------------------------------------------------------------------------
# Plugin / Skill errors
# ---------------------------------------------------------------------------


class PluginLoadError(NagiFlowError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    detail = "Failed to load plugin."


class SkillExecutionError(NagiFlowError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    detail = "Skill execution failed."


# ---------------------------------------------------------------------------
# File / Workspace errors
# ---------------------------------------------------------------------------


class WorkspaceError(NagiFlowError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    detail = "Workspace operation failed."


class UnsupportedFileTypeError(NagiFlowError):
    status_code = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    detail = "File type is not supported."
