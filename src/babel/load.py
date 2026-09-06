"""Load .babel trees from disk. Metadata only — never executes application code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REQUIRED_TREE = (
    "manifest.yml",
    "capabilities.yml",
    "relations.yml",
)


def read_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(str(path))
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return None
    return yaml.safe_load(text)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_catalog_root() -> Path:
    env = Path.cwd()
    if (env / ".babel" / "ecosystem.yml").exists():
        return env
    packaged = package_root()
    if (packaged / ".babel" / "ecosystem.yml").exists():
        return packaged
    return env


def load_manifest_dir(babel_dir: Path) -> dict[str, Any]:
    babel_dir = babel_dir.resolve()
    data: dict[str, Any] = {"path": str(babel_dir)}
    for name in REQUIRED_TREE:
        data[name.split(".")[0]] = read_yaml(babel_dir / name)
    schemas_dir = babel_dir / "schemas"
    examples_dir = babel_dir / "examples"
    data["schemas"] = {}
    if schemas_dir.is_dir():
        for p in sorted(schemas_dir.iterdir()):
            if p.suffix == ".json":
                data["schemas"][p.name] = read_json(p)
            elif p.suffix in {".yml", ".yaml"}:
                data["schemas"][p.name] = read_yaml(p)
    data["examples"] = {}
    if examples_dir.is_dir():
        for p in sorted(examples_dir.iterdir()):
            if p.suffix == ".json":
                data["examples"][p.name] = read_json(p)
            elif p.suffix in {".yml", ".yaml"}:
                data["examples"][p.name] = read_yaml(p)
    return data


def load_ecosystem(root: Path | None = None) -> dict[str, Any]:
    root = (root or default_catalog_root()).resolve()
    eco_path = root / ".babel" / "ecosystem.yml"
    eco = read_yaml(eco_path) or {}
    eco["_root"] = str(root)
    eco["_path"] = str(eco_path)
    return eco
