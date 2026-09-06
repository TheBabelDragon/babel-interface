"""Exact capability resolution. No fuzzy matching at execution time."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import CapabilityNotFound, RepositoryNotFound
from .load import default_catalog_root
from .validate import lookup_schema_document, resolve_repo_babel_dir, validate_tree


@dataclass
class Capability:
    repository: str
    id: str
    description: str
    input_schema: dict[str, Any] | None
    output_schema: dict[str, Any] | None
    input_schema_ref: str | None
    output_schema_ref: str | None
    invocation: dict[str, Any] | None
    effects: list[str]
    operation: str
    safe: bool
    babel_dir: Path
    adapter_root: Path
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def invocable(self) -> bool:
        return isinstance(self.invocation, dict) and bool(self.invocation.get("executable"))


def _matches(cap: dict[str, Any], capability: str) -> bool:
    names = {
        str(cap.get("name") or ""),
        str(cap.get("id") or ""),
    }
    names.update(str(a) for a in (cap.get("aliases") or []))
    names.discard("")
    return capability in names


def resolve_capability(
    repository: str,
    capability: str,
    root: Path | None = None,
) -> Capability:
    root = Path(root or default_catalog_root()).resolve()
    result = validate_tree(root)
    loaded = result.get("loaded") or {}
    if repository not in loaded:
        known = sorted(loaded.keys())
        raise RepositoryNotFound(
            f"unknown repository '{repository}'",
            extra={"known": known},
        )
    repo = loaded[repository]
    caps = repo.get("capabilities") or []
    matches = [c for c in caps if _matches(c, capability)]
    if not matches:
        available = [c.get("id") or c.get("name") for c in caps]
        raise CapabilityNotFound(
            f"unknown capability '{repository}:{capability}'",
            extra={"known": available},
        )
    if len(matches) != 1:
        raise CapabilityNotFound(
            f"capability '{repository}:{capability}' is not unique",
            extra={"matches": [c.get("name") for c in matches]},
        )
    cap = matches[0]
    schema_docs = repo.get("schema_docs") or {}
    babel_dir = Path(repo["babel_dir"])
    return Capability(
        repository=repository,
        id=str(cap.get("id") or cap.get("name")),
        description=str(cap.get("description") or ""),
        input_schema=lookup_schema_document(schema_docs, cap.get("input_schema")),
        output_schema=lookup_schema_document(schema_docs, cap.get("output_schema") or cap.get("schema")),
        input_schema_ref=cap.get("input_schema"),
        output_schema_ref=cap.get("output_schema") or cap.get("schema"),
        invocation=cap.get("invocation"),
        effects=list(cap.get("effects") or cap.get("side_effects") or []),
        operation=str(cap.get("operation") or "compute"),
        safe=bool(cap.get("safe")),
        babel_dir=babel_dir,
        adapter_root=babel_dir.parent,
        raw=cap,
    )
