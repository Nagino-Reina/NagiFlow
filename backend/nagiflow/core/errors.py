"""Consistent error envelope with stable machine codes (docs/05 §3, docs/15 §6).

Domain/service code raises `AppError(code=...)`; the API layer renders it as:
    {"error": {"code", "message", "details", "correlation_id"}}
Provider failures are isolated and surfaced rather than crashing the request.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """A domain error carrying a stable code + HTTP status."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def envelope(self, correlation_id: str | None = None) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "correlation_id": correlation_id,
            }
        }


# --- common factories (stable codes mirror docs/05 §3) ---


def not_found(resource: str, _id: str) -> AppError:
    return AppError(
        f"{resource}.not_found",
        f"No {resource} with id '{_id}'.",
        status_code=404,
        details={"id": _id},
    )


def validation_failed(message: str, details: dict[str, Any] | None = None) -> AppError:
    return AppError("validation.failed", message, status_code=422, details=details)


def auth_required() -> AppError:
    return AppError("auth.required", "Authentication required.", status_code=401)


def forbidden(code: str = "auth.forbidden", message: str = "Forbidden.") -> AppError:
    return AppError(code, message, status_code=403)


def guest_upgrade_required() -> AppError:
    return AppError(
        "guest.upgrade_required",
        "Log in to a local account to perform this action.",
        status_code=403,
    )


def conflict(code: str, message: str) -> AppError:
    return AppError(code, message, status_code=409)


def provider_unavailable(provider: str) -> AppError:
    return AppError(
        "provider.unavailable",
        f"Provider '{provider}' is unavailable.",
        status_code=503,
        details={"provider": provider},
    )


def provider_error(provider: str, message: str) -> AppError:
    return AppError(
        "provider.error",
        f"Provider '{provider}' failed: {message}",
        status_code=502,
        details={"provider": provider},
    )


def capability_unsupported(feature: str) -> AppError:
    return AppError(
        "provider.capability_unsupported",
        f"The active provider does not support '{feature}'.",
        status_code=422,
        details={"feature": feature},
    )
