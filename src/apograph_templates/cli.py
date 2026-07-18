"""Command-line interface for discovering and installing Apograph templates."""

from __future__ import annotations

import argparse
from difflib import get_close_matches
from pathlib import Path
import sys
from typing import Sequence, TextIO

from . import PRODUCT_NAME, __version__
from .errors import ApographError
from .install import install_template
from .remote import (
    GitHubReleaseSource,
    ResolvedRelease,
    catalog_template,
    catalog_templates,
)


def _add_release_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--version",
        dest="release_version",
        metavar="TAG",
        help="published collection version, such as v0.2.0 (default: newest published)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apograph",
        description="Discover and install verified Apograph template artifacts.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PRODUCT_NAME} {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list published templates")
    _add_release_argument(list_parser)

    info_parser = subparsers.add_parser("info", help="show one template's metadata")
    info_parser.add_argument("template_id")
    _add_release_argument(info_parser)

    new_parser = subparsers.add_parser("new", help="create a project from a template")
    new_parser.add_argument("template_id")
    new_parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        help="new directory (default: ./<template-id>)",
    )
    _add_release_argument(new_parser)
    return parser


def _resolve(
    source: GitHubReleaseSource, version: str | None, output: TextIO
) -> ResolvedRelease:
    release = source.resolve(version)
    print(f"Release: {release.tag}", file=output)
    return release


def _print_list(release: ResolvedRelease, output: TextIO) -> None:
    templates = catalog_templates(release)
    columns = (
        ("ID", [template["id"] for template in templates]),
        ("FORMAT", [template["format"] for template in templates]),
        ("STATUS", [template["status"] for template in templates]),
        ("NAME", [template["name"] for template in templates]),
    )
    widths = [max(len(header), *(len(str(value)) for value in values)) for header, values in columns]
    print(
        "  ".join(header.ljust(width) for (header, _), width in zip(columns, widths)),
        file=output,
    )
    for row in zip(*(values for _, values in columns)):
        print(
            "  ".join(str(value).ljust(width) for value, width in zip(row, widths)),
            file=output,
        )


def _suggest_template(release: ResolvedRelease, template_id: str) -> str | None:
    template_ids = [template["id"] for template in catalog_templates(release)]
    matches = get_close_matches(template_id, template_ids, n=1, cutoff=0.45)
    return matches[0] if matches else None


def _find_template(release: ResolvedRelease, template_id: str) -> dict:
    try:
        return catalog_template(release, template_id)
    except ApographError as exc:
        suggestion = _suggest_template(release, template_id)
        if suggestion:
            raise ApographError(f"{exc}. Did you mean {suggestion!r}?") from exc
        raise


def _print_info(release: ResolvedRelease, template: dict, output: TextIO) -> None:
    institution = template["institution"]
    license_data = template["license"]
    fields = [
        ("ID", template["id"]),
        ("Name", template["name"]),
        ("Purpose", template["purpose"]),
        ("Format", template["format"]),
        ("Status", template["status"]),
        (
            "Institution",
            f"{institution['name']} ({institution['relationship']})",
        ),
        ("Compiler", template["compiler"]),
        ("License", license_data["expression"]),
        ("Release", release.tag),
    ]
    width = max(len(label) for label, _ in fields)
    for label, value in fields:
        print(f"{label.ljust(width)}  {value}", file=output)
    print(file=output)
    print(template["description"], file=output)


def main(
    argv: Sequence[str] | None = None,
    *,
    source: GitHubReleaseSource | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI and return a process exit code."""
    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    args = build_parser().parse_args(argv)
    release_source = source or GitHubReleaseSource()
    try:
        release = _resolve(release_source, args.release_version, output)
        if args.command == "list":
            _print_list(release, output)
        elif args.command == "info":
            template = _find_template(release, args.template_id)
            _print_info(release, template, output)
        elif args.command == "new":
            template = _find_template(release, args.template_id)
            destination = args.destination or Path(template["id"])
            installed = install_template(
                release_source, release, template["id"], destination
            )
            print(f"Created {template['name']} in {installed}", file=output)
            print(f"Next: read {installed / 'README.md'}", file=output)
        else:  # pragma: no cover - argparse enforces the command set
            raise AssertionError(f"unsupported command: {args.command}")
    except ApographError as exc:
        print(f"apograph: error: {exc}", file=errors)
        return 1
    return 0


def entrypoint() -> None:
    """Console-script entry point."""
    raise SystemExit(main())
