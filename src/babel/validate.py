"""Validate .babel trees and emit a normalized capability graph.

Descriptive only. Never executes application code, never rewrites PHY
assumptions, never mutates a participating repository.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import (
    CAPABILITY_FIELDS,
    OWNER,
    PROTOCOL,
    RELATION_TYPES,
    __version__,
)
from .load import default_catalog_root, load_ecosystem, load_manifest_dir

MUTATING_OPERATIONS = frozenset({"mutate", "control"})


def resolve_repo_babel_dir(
    root: Path,
    name: str,
    spec: dict[str, Any] | None = None,
) -> Path | None:
    """Locate the on-disk .babel tree for a catalogued repository.

    Resolution order:
      1. spec['babel_path'] relative to the catalog root
      2. adapters/<name>/.babel  (offline catalog copies)
      3. <root>/.babel when this tree *is* the named protocol repo
    """
    root = Path(root).resolve()
    spec = spec or {}
    candidates: list[Path] = []
    babel_path = spec.get("babel_path")
    if babel_path:
        candidates.append(root / str(babel_path))
    candidates.append(root / "adapters" / name / ".babel")
    role = spec.get("role")
    if name == "babel-interface" or role == "protocol":
        candidates.append(root / ".babel")

    seen: set[Path] = set()
    for cand in candidates:
        try:
            cand = cand.resolve()
        except OSError:
            continue
        if cand in seen:
            continue
        seen.add(cand)
        if cand.is_dir() and (cand / "manifest.yml").exists():
            return cand
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _capability_records(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("capabilities") or raw.get("items") or []
        if isinstance(items, dict):
            items = [
                {**v, "name": k} if isinstance(v, dict) else {"name": k}
                for k, v in items.items()
            ]
    else:
        return []
    out: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            out.append({"name": item})
        elif isinstance(item, dict):
            out.append(dict(item))
    return out


def _relation_map(raw: Any) -> dict[str, list[str]]:
    if not raw:
        return {}
    body = raw.get("relations") if isinstance(raw, dict) and "relations" in raw else raw
    if not isinstance(body, dict):
        return {}
    mapped: dict[str, list[str]] = {}
    for key, value in body.items():
        if key.startswith("_"):
            continue
        names = []
        for item in _as_list(value):
            if isinstance(item, str) and item:
                names.append(item)
            elif isinstance(item, dict):
                target = item.get("to") or item.get("name") or item.get("repo")
                if target:
                    names.append(str(target))
        if names:
            mapped[str(key)] = names
    return mapped


def _validate_capability(repo: str, cap: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    name = cap.get("name") or "<unnamed>"
    prefix = f"{repo}.capability[{name}]"
    for field in CAPABILITY_FIELDS:
        if field not in cap:
            errors.append(f"{prefix}: missing required field '{field}'")
    operation = cap.get("operation")
    if operation is not None and not isinstance(operation, str):
        errors.append(f"{prefix}: operation must be a string")
    side_effects = cap.get("side_effects")
    if operation in MUTATING_OPERATIONS:
        if not side_effects:
            errors.append(
                f"{prefix}: operation '{operation}' must declare side_effects"
            )
    if "safe" in cap and cap["safe"] is False and not side_effects:
        errors.append(f"{prefix}: unsafe capability must declare side_effects")
    return errors


def _validate_repo(
    name: str,
    spec: dict[str, Any],
    tree: dict[str, Any],
    known: dict[str, Any],
) -> tuple[list[str], dict[str, Any], list[dict[str, str]]]:
    errors: list[str] = []
    manifest = tree.get("manifest") or {}
    if not isinstance(manifest, dict):
        errors.append(f"{name}: manifest.yml is not a mapping")
        manifest = {}

    for field in ("babel", "identity", "purpose", "status"):
        if field not in manifest:
            errors.append(f"{name}: manifest missing '{field}'")

    identity = manifest.get("identity") or {}
    if isinstance(identity, dict):
        ident_name = identity.get("name")
        if ident_name and ident_name != name:
            errors.append(
                f"{name}: identity.name '{ident_name}' does not match catalog name"
            )
    else:
        errors.append(f"{name}: manifest.identity must be a mapping")
        identity = {}

    capabilities = _capability_records(tree.get("capabilities"))
    if not capabilities:
        capabilities = _capability_records(manifest.get("capabilities"))
    for cap in capabilities:
        errors.extend(_validate_capability(name, cap))

    relations = _relation_map(tree.get("relations"))
    for rel_type in RELATION_TYPES:
        extra = spec.get(rel_type)
        if extra:
            existing = list(relations.get(rel_type) or [])
            for item in _as_list(extra):
                target = item if isinstance(item, str) else None
                if target and target not in existing:
                    existing.append(target)
            if existing:
                relations[rel_type] = existing

    catalog_names = set(known.keys())
    known_full = {str(v) for v in known.values()}
    edges: list[dict[str, str]] = []
    for rel_type, targets in relations.items():
        if rel_type not in RELATION_TYPES:
            errors.append(f"{name}: unknown relation type '{rel_type}'")
            continue
        for target in targets:
            short = str(target).split("/")[-1]
            if rel_type != "isolates" and "/" in str(target):
                if short not in catalog_names and str(target) not in known_full:
                    errors.append(
                        f"{name}: relation {rel_type} -> '{target}' "
                        "is not a catalogued or known repository"
                    )
            edges.append({"from": name, "type": rel_type, "to": short})

    schemas = tree.get("schemas") or {}
    if not isinstance(schemas, dict):
        errors.append(f"{name}: schemas/ did not load as a mapping")
        schemas = {}
    else:
        for fname, doc in schemas.items():
            if not isinstance(doc, dict):
                errors.append(f"{name}: schema '{fname}' is not an object")

    examples = tree.get("examples") or {}

    repo_obj = {
        "name": name,
        "repo": spec.get("repo") or (identity.get("repo") if identity else name),
        "url": spec.get("url") or (identity.get("url") if identity else None),
        "role": spec.get("role") or (identity.get("kind") if identity else None),
        "status": manifest.get("status"),
        "purpose": manifest.get("purpose"),
        "babel_dir": tree.get("path"),
        "capabilities": capabilities,
        "relations": relations,
        "schemas": sorted(schemas.keys()),
        "examples": sorted(examples.keys()) if isinstance(examples, dict) else [],
        "produces": _as_list(spec.get("produces")),
        "consumes": _as_list(spec.get("consumes")),
        "isolates": _as_list(spec.get("isolates")),
        "pages": spec.get("pages"),
    }
    return errors, repo_obj, edges


def validate_tree(root: Path | str | None = None) -> dict[str, Any]:
    """Walk the catalog and return a structured validation result."""
    root = Path(root or default_catalog_root()).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    repositories: dict[str, Any] = {}
    edges: list[dict[str, str]] = []

    try:
        eco = load_ecosystem(root)
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "errors": [f"missing ecosystem: {exc}"],
            "warnings": [],
            "root": str(root),
            "repositories": {},
            "edges": [],
        }

    catalog = eco.get("repositories") or {}
    if not isinstance(catalog, dict) or not catalog:
        errors.append("ecosystem.yml has no repositories")

    known: dict[str, Any] = dict(eco.get("known_repositories") or {})
    for name, spec in catalog.items():
        if isinstance(spec, dict) and spec.get("repo"):
            known.setdefault(name, spec["repo"])
        else:
            known.setdefault(name, name)

    for name, spec in catalog.items():
        if not isinstance(spec, dict):
            errors.append(f"{name}: catalog entry is not a mapping")
            continue
        babel_dir = resolve_repo_babel_dir(root, name, spec)
        if babel_dir is None:
            errors.append(
                f"{name}: no .babel tree (looked at {spec.get('babel_path')!r} "
                f"and adapters/{name}/.babel)"
            )
            continue
        try:
            tree = load_manifest_dir(babel_dir)
        except FileNotFoundError as exc:
            errors.append(f"{name}: incomplete .babel tree ({exc})")
            continue
        repo_errors, repo_obj, repo_edges = _validate_repo(name, spec, tree, known)
        errors.extend(repo_errors)
        repositories[name] = repo_obj
        edges.extend(repo_edges)

    uniq: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge["from"], edge["type"], edge["to"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(edge)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "root": str(root),
        "ecosystem": eco.get("name"),
        "protocol": str(eco.get("babel") or PROTOCOL),
        "owner": eco.get("owner") or OWNER,
        "repositories": repositories,
        "edges": uniq,
    }


def emit_normalized(result: dict[str, Any]) -> dict[str, Any]:
    """Public, JSON-serializable capability graph."""
    return {
        "ok": bool(result.get("ok")),
        "protocol": result.get("protocol") or PROTOCOL,
        "version": __version__,
        "owner": result.get("owner") or OWNER,
        "ecosystem": result.get("ecosystem"),
        "root": result.get("root"),
        "repositories": result.get("repositories") or {},
        "edges": result.get("edges") or [],
        "errors": result.get("errors") or [],
        "warnings": result.get("warnings") or [],
    }
