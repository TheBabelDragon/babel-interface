"""JSON Schema subset used by both `babel validate` and `babel invoke`.

This is the single schema implementation. It covers the fragment actually
used by Babel adapter contracts: type, required, properties, items, enum,
minimum/maximum, minLength, additionalProperties, const.
"""

from __future__ import annotations

from typing import Any


def _path(prefix: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{prefix}[{key}]"
    if prefix == "$":
        return f"$.{key}"
    return f"{prefix}.{key}"


def validate_against_schema(
    instance: Any,
    schema: dict[str, Any] | None,
    *,
    path: str = "$",
) -> list[dict[str, str]]:
    """Return a list of {path, message} errors. Empty means valid."""
    if not schema:
        return []
    errors: list[dict[str, str]] = []

    if "const" in schema and instance != schema["const"]:
        errors.append({"path": path, "message": f"Expected const {schema['const']!r}"})
        return errors

    expected = schema.get("type")
    if expected is not None:
        types = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(instance, t) for t in types):
            errors.append({"path": path, "message": f"Expected {expected}"})
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append({"path": path, "message": f"Expected one of {schema['enum']!r}"})

    if isinstance(instance, str) and "minLength" in schema:
        if len(instance) < int(schema["minLength"]):
            errors.append({"path": path, "message": f"Expected minLength {schema['minLength']}"})

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append({"path": path, "message": f"Expected minimum {schema['minimum']}"})
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append({"path": path, "message": f"Expected maximum {schema['maximum']}"})
        if schema.get("type") == "integer" and not isinstance(instance, int):
            errors.append({"path": path, "message": "Expected integer"})

    if isinstance(instance, dict) and (expected in (None, "object") or "object" in (expected if isinstance(expected, list) else [expected])):
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                errors.append({"path": _path(path, key), "message": "Missing required property"})
        props = schema.get("properties") or {}
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                errors.extend(validate_against_schema(value, props[key], path=_path(path, key)))
            elif additional is False:
                errors.append({"path": _path(path, key), "message": "Unexpected property"})
            elif isinstance(additional, dict):
                errors.extend(validate_against_schema(value, additional, path=_path(path, key)))

    if isinstance(instance, list) and "items" in schema:
        item_schema = schema["items"]
        if isinstance(item_schema, dict):
            for i, item in enumerate(instance):
                errors.extend(validate_against_schema(item, item_schema, path=_path(path, i)))

    return errors


def _matches_type(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    return True


def first_error_message(errors: list[dict[str, str]]) -> tuple[str, str]:
    if not errors:
        return "$", ""
    return errors[0].get("path", "$"), errors[0].get("message", "invalid")
