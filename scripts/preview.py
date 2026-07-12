#!/usr/bin/env python3
"""Compile catalog entry points for local development previews.

Release previews are produced by ``pack.py`` from the isolated packed artifact.
This command remains a source-tree convenience and uses the same compiler API.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from apograph.compile import CompilationError, compile_entrypoints
from catalog import PUBLIC_STATUSES, load_catalog, require_valid_catalog, select_entrypoint


REPO_ROOT = Path(__file__).resolve().parent.parent


def compile_template(template: dict) -> bool:
    source_dir = REPO_ROOT / template["source_dir"]
    preview_entry = select_entrypoint(template, preview=True)
    try:
        results = compile_entrypoints(
            template,
            source_dir,
            source_dir / "out",
            entrypoints=[preview_entry],
            source_shared_dir=REPO_ROOT / "shared" / "latex"
            if template.get("format") == "latex"
            else None,
            synctex=True,
        )
    except CompilationError as exc:
        print(f"  Compilation failed: {exc}", file=sys.stderr)
        if exc.output:
            for line in exc.output.splitlines()[-40:]:
                print(f"    {line}", file=sys.stderr)
        return False

    preview_path = source_dir.parent / "preview.pdf"
    shutil.copyfile(results[0].pdf_path, preview_path)
    print(f"  Preview: {preview_path.relative_to(REPO_ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile local source previews.")
    parser.add_argument("template_id", nargs="?", help="exact template ID; defaults to all public entries")
    parser.add_argument("--list", action="store_true", help="list catalog entries")
    args = parser.parse_args()

    catalog = load_catalog()
    require_valid_catalog(catalog)
    templates = catalog.get("templates", [])
    if args.list:
        for template in templates:
            print(f"{template['id']:45s} {template['status']:10s} {template['name']}")
        return 0

    if args.template_id:
        selected = [template for template in templates if template["id"] == args.template_id]
        if not selected:
            print(f"Unknown template ID: {args.template_id}", file=sys.stderr)
            return 1
    else:
        selected = [template for template in templates if template["status"] in PUBLIC_STATUSES]
        if not selected:
            print("No beta/stable templates are eligible for default preview compilation.")
            return 0

    failures = []
    for template in selected:
        print(f"Compiling {template['id']}")
        if not compile_template(template):
            failures.append(template["id"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
