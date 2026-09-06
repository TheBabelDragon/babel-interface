"""Typed invocation errors. Codes are stable machine values."""

from __future__ import annotations

from typing import Any


class BabelError(Exception):
    code = "BABEL_ERROR"

    def __init__(self, message: str, *, path: str | None = None, extra: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.path = path
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path:
            payload["path"] = self.path
        payload.update(self.extra)
        return payload


class RepositoryNotFound(BabelError):
    code = "REPOSITORY_NOT_FOUND"


class CapabilityNotFound(BabelError):
    code = "CAPABILITY_NOT_FOUND"


class CapabilityNotInvocable(BabelError):
    code = "CAPABILITY_NOT_INVOCABLE"


class InputMalformed(BabelError):
    code = "INPUT_MALFORMED"


class InputSchemaInvalid(BabelError):
    code = "INPUT_SCHEMA_INVALID"


class OutputSchemaInvalid(BabelError):
    code = "ADAPTER_OUTPUT_INVALID"


class AdapterTimeout(BabelError):
    code = "TIMEOUT"


class AdapterFailed(BabelError):
    code = "ADAPTER_FAILED"


class AdapterOutputMalformed(BabelError):
    code = "ADAPTER_OUTPUT_MALFORMED"


class EffectDenied(BabelError):
    code = "EFFECT_DENIED"


class InvocationDenied(BabelError):
    code = "INVOCATION_DENIED"
