#!/usr/bin/env python3
"""Build deterministic, self-contained Apograph release artifacts."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from apograph.artifacts import ArtifactError, build_artifact
from catalog import PUBLIC_STATUSES, load_catalog, require_valid_catalog


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "build"


def find_template(catalog: dict, template_id: str) -> dict | None:
    return next(
        (template for template in catalog.get("templates", []) if template["id"] == template_id),
        None,
    )


def _build_one(template: dict, catalog: dict, args: argparse.Namespace) -> bool:
    print(f"Building {template['id']} ({args.mode} mode)")
    try:
        result = build_artifact(
            template,
            args.out,
            repo_root=REPO_ROOT,
            catalog_schema_version=catalog["schema_version"],
            release_version=catalog["release_version"],
            source_commit=args.source_commit,
            source_date_epoch=args.source_date_epoch,
            include_vscode=not args.no_vscode,
            fetch_assets=args.fetch_assets,
            verify=not args.skip_compile,
            release_mode=args.mode == "release",
            force=args.force,
            keep_failed=args.keep_failed,
        )
    except ArtifactError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if exc.debug_dir is not None:
            print(f"Debug artifact preserved at: {exc.debug_dir}", file=sys.stderr)
        return False

    print(f"  ZIP:      {result.zip_path}")
    print(f"  SHA-256:  {result.sha256}")
    print(f"  Files:    {result.file_count}")
    print(f"  Report:   {result.report_path}")
    if result.preview_path:
        print(f"  Preview:  {result.preview_path}")
    if args.skip_compile:
        print("  WARNING: compilation skipped; this is not a release verification")
    else:
        print(f"  Compiled: {len(result.compilation_results)} entry point(s)")
    return True


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Build deterministic, self-contained Apograph artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/pack.py presentation-beamer-polito-latex\n"
            "  python3 scripts/pack.py presentation-beamer-polito-latex --force\n"
            "  python3 scripts/pack.py --all --mode release --source-commit <sha>\n"
        ),
    )
    selection = command.add_mutually_exclusive_group(required=True)
    selection.add_argument("template_id", nargs="?", help="exact catalog template ID")
    selection.add_argument("--all", action="store_true", help="build all beta/stable entries")
    command.add_argument(
        "--mode",
        choices=("developer", "release"),
        default="developer",
        help="developer permits drafts; release accepts only beta/stable (default: developer)",
    )
    command.add_argument(
        "--out", type=Path, default=DEFAULT_OUTPUT_DIR, help=f"output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    command.add_argument(
        "--force", action="store_true", help="replace this template's existing artifact outputs"
    )
    command.add_argument(
        "--skip-compile",
        action="store_true",
        help="developer-only: build without the mandatory isolated compile check",
    )
    command.add_argument(
        "--fetch-assets",
        action="store_true",
        help="fetch only catalog assets declared mode=fetched and verify their checksums",
    )
    command.add_argument(
        "--no-vscode", action="store_true", help="omit generated VS Code recommendations"
    )
    command.add_argument(
        "--keep-failed", action="store_true", help="preserve the temporary artifact after failure"
    )
    command.add_argument(
        "--source-commit",
        default=os.environ.get("GITHUB_SHA"),
        help="commit identifier recorded in metadata (default: GITHUB_SHA if set)",
    )
    command.add_argument(
        "--source-date-epoch",
        type=int,
        help="normalized build timestamp (default: SOURCE_DATE_EPOCH or 1980-01-01)",
    )
    return command


def main() -> int:
    args = parser().parse_args()
    if args.mode == "release" and args.skip_compile:
        print("Error: --skip-compile is not permitted in release mode", file=sys.stderr)
        return 2

    try:
        catalog = load_catalog()
        require_valid_catalog(catalog)
    except Exception as exc:
        print(f"Catalog validation failed: {exc}", file=sys.stderr)
        return 1

    if args.all:
        templates = [
            template
            for template in catalog.get("templates", [])
            if template.get("status") in PUBLIC_STATUSES
        ]
        if not templates:
            print("No beta/stable templates are eligible for artifact building.", file=sys.stderr)
            return 1
    else:
        template = find_template(catalog, args.template_id)
        if template is None:
            available = ", ".join(item["id"] for item in catalog.get("templates", []))
            print(f"Unknown template ID: {args.template_id}", file=sys.stderr)
            print(f"Available: {available}", file=sys.stderr)
            return 1
        templates = [template]

    failed = False
    for template in templates:
        if not _build_one(template, catalog, args):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
