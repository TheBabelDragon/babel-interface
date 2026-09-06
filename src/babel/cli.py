"""Read-only Babel discovery CLI. JSON on stdout. No credentials. No mutation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import PROTOCOL, __version__
from .graph import capabilities, discover, inspect, relations, schema
from .validate import emit_normalized, validate_tree


def _dump(obj) -> int:
    json.dump(obj, sys.stdout, indent=2, sort_keys=False, default=str)
    sys.stdout.write("\n")
    return 0 if obj.get("ok", True) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="babel",
        description="Discover TheBabelDragon repositories as typed components.",
    )
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="cmd")

    def attach(p):
        p.add_argument("--root", type=Path, default=None, help="Catalog root")
        return p

    attach(sub.add_parser("discover", help="Return the complete normalized capability graph"))
    p_ins = attach(sub.add_parser("inspect", help="Inspect one repository"))
    p_ins.add_argument("name")
    p_cap = attach(sub.add_parser("capabilities", help="List capabilities"))
    p_cap.add_argument("name", nargs="?")
    p_sch = attach(sub.add_parser("schema", help="Read a machine-readable schema"))
    p_sch.add_argument("ref", help="filename or repo:filename")
    p_rel = attach(sub.add_parser("relations", help="Typed repository relationships"))
    p_rel.add_argument("name", nargs="?")
    attach(sub.add_parser("validate", help="Validate every manifest in the catalog"))

    args = parser.parse_args(argv)
    if args.version:
        return _dump({"ok": True, "version": __version__, "protocol": PROTOCOL})
    if not args.cmd:
        parser.print_help()
        return 2

    root = getattr(args, "root", None)
    if args.cmd == "discover":
        return _dump(discover(root))
    if args.cmd == "inspect":
        return _dump(inspect(args.name, root))
    if args.cmd == "capabilities":
        return _dump(capabilities(args.name, root))
    if args.cmd == "schema":
        return _dump(schema(args.ref, root))
    if args.cmd == "relations":
        return _dump(relations(args.name, root))
    if args.cmd == "validate":
        result = validate_tree(root)
        out = emit_normalized(result)
        out["command"] = "validate"
        return _dump(out)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
