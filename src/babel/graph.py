"""Query helpers over the normalized capability graph."""

from __future__ import annotations

from typing import Any

from .load import default_catalog_root
from .validate import emit_normalized, validate_tree


def discover(root=None) -> dict[str, Any]:
    result = validate_tree(root or default_catalog_root())
    return emit_normalized(result)


def inspect(name: str, root=None) -> dict[str, Any]:
    graph = discover(root)
    repo = (graph.get("repositories") or {}).get(name)
    if repo is None:
        return {
            "ok": False,
            "error": f"unknown repository '{name}'",
            "known": sorted((graph.get("repositories") or {}).keys()),
        }
    edges = [e for e in graph.get("edges") or [] if e.get("from") == name or e.get("to") == name]
    return {"ok": True, "name": name, "repository": repo, "edges": edges}


def capabilities(name: str | None = None, root=None) -> dict[str, Any]:
    graph = discover(root)
    repos = graph.get("repositories") or {}
    if name:
        repo = repos.get(name)
        if repo is None:
            return {"ok": False, "error": f"unknown repository '{name}'"}
        return {"ok": True, "repository": name, "capabilities": repo.get("capabilities") or []}
    out = {n: (r.get("capabilities") or []) for n, r in repos.items()}
    return {"ok": True, "capabilities": out}


def schema(ref: str, root=None) -> dict[str, Any]:
    """Look up a schema by repo:filename or filename."""
    from pathlib import Path

    from .validate import resolve_repo_babel_dir
    from .load import load_ecosystem, load_manifest_dir

    root = root or default_catalog_root()
    eco = load_ecosystem(root)
    repos = eco.get("repositories") or {}
    repo_name = None
    filename = ref
    if ":" in ref:
        repo_name, filename = ref.split(":", 1)
    if not filename.endswith(".json") and "." not in filename:
        filename = filename + ".schema.json"
        alt = filename
    else:
        alt = filename

    matches = []
    targets = [repo_name] if repo_name else list(repos.keys())
    for name in targets:
        spec = repos.get(name) or {}
        babel_dir = resolve_repo_babel_dir(Path(root), name, spec)
        if babel_dir is None:
            continue
        tree = load_manifest_dir(babel_dir)
        schemas = tree.get("schemas") or {}
        if filename in schemas:
            matches.append({"repository": name, "file": filename, "schema": schemas[filename]})
        elif alt in schemas:
            matches.append({"repository": name, "file": alt, "schema": schemas[alt]})
        else:
            for key, doc in schemas.items():
                if filename in key or filename.replace(".schema.json", "") in key:
                    matches.append({"repository": name, "file": key, "schema": doc})
    if not matches:
        return {"ok": False, "error": f"schema '{ref}' not found"}
    return {"ok": True, "matches": matches}


def relations(name: str | None = None, root=None) -> dict[str, Any]:
    graph = discover(root)
    edges = graph.get("edges") or []
    if name:
        edges = [e for e in edges if e.get("from") == name or e.get("to") == name]
        repo = (graph.get("repositories") or {}).get(name)
        if repo is None:
            return {"ok": False, "error": f"unknown repository '{name}'"}
        return {"ok": True, "repository": name, "relations": repo.get("relations") or {}, "edges": edges}
    return {"ok": True, "edges": edges}
