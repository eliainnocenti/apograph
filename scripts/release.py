#!/usr/bin/env python3
"""Validate and assemble Apograph release-candidate metadata."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

try:
    from . import catalog as catalog_module
    from .apograph.artifacts import sha256_file
except ImportError:  # Direct execution from scripts/.
    import catalog as catalog_module
    from apograph.artifacts import sha256_file


REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"


class ReleaseError(RuntimeError):
    """Raised when release-candidate evidence is incomplete or inconsistent."""


def validate_release_tag(catalog: dict[str, Any], tag: str, changelog: str) -> str:
    """Validate that a publication tag matches catalog and changelog versions."""
    if not tag.startswith("v") or len(tag) == 1:
        raise ReleaseError("release tag must use the form v<release_version>")
    version = tag[1:]
    expected = catalog["release_version"]
    if version != expected:
        raise ReleaseError(
            f"tag {tag} does not match catalog release_version {expected}"
        )
    if version.endswith("-dev"):
        raise ReleaseError("development release_version values may not be published")
    heading = re.compile(
        rf"^##\s+(?:{re.escape(version)}|\[{re.escape(version)}\])(?:\s+[-—].*)?$",
        re.MULTILINE,
    )
    if not heading.search(changelog):
        raise ReleaseError(f"CHANGELOG.md has no release heading for {version}")
    return version


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseError(f"missing release file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"{path.name} must contain a JSON object")
    return value


def _verify_checksum(path: Path, expected: str, context: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise ReleaseError(
            f"checksum mismatch for {context}: expected {expected}, got {actual}"
        )


def assemble_release_candidate(
    catalog: dict[str, Any],
    build_dir: Path,
    *,
    source_commit: str,
    tag: Optional[str] = None,
) -> dict[str, Any]:
    """Verify tested build outputs and write a catalog snapshot plus release index."""
    build_dir = build_dir.resolve()
    if not build_dir.is_dir():
        raise ReleaseError(f"build directory does not exist: {build_dir}")
    public = catalog_module.public_templates(catalog)
    if not public:
        raise ReleaseError("catalog has no beta/stable templates to release")

    expected_reports = {f"{template['id']}.build.json" for template in public}
    actual_reports = {path.name for path in build_dir.glob("*.build.json")}
    if actual_reports != expected_reports:
        missing = sorted(expected_reports - actual_reports)
        unexpected = sorted(actual_reports - expected_reports)
        details = []
        if missing:
            details.append(f"missing reports: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected reports: {', '.join(unexpected)}")
        raise ReleaseError("release report set mismatch; " + "; ".join(details))

    template_entries: list[dict[str, Any]] = []
    source_epochs: set[int] = set()
    for template in public:
        template_id = template["id"]
        report_name = f"{template_id}.build.json"
        report = _read_json(build_dir / report_name)
        if report.get("template_id") != template_id:
            raise ReleaseError(f"{report_name} template_id does not match {template_id}")
        if report.get("mode") != "release":
            raise ReleaseError(f"{report_name} was not produced in release mode")
        if report.get("source_commit") != source_commit:
            raise ReleaseError(f"{report_name} source_commit does not match {source_commit}")
        if report.get("release_version") != catalog["release_version"]:
            raise ReleaseError(f"{report_name} release_version does not match the catalog")
        if report.get("status") not in catalog_module.PUBLIC_STATUSES:
            raise ReleaseError(f"{report_name} does not describe a public template")

        epoch = report.get("source_date_epoch")
        if not isinstance(epoch, int):
            raise ReleaseError(f"{report_name} has no integer source_date_epoch")
        source_epochs.add(epoch)

        artifact = report.get("artifact")
        if not isinstance(artifact, dict):
            raise ReleaseError(f"{report_name} has no artifact record")
        zip_name = artifact.get("path")
        zip_sha256 = artifact.get("sha256")
        if not isinstance(zip_name, str) or not isinstance(zip_sha256, str):
            raise ReleaseError(f"{report_name} has an invalid artifact record")
        zip_path = build_dir / zip_name
        if not zip_path.is_file():
            raise ReleaseError(f"missing release ZIP: {zip_name}")
        _verify_checksum(zip_path, zip_sha256, zip_name)

        checksum_name = f"{zip_name}.sha256"
        checksum_path = build_dir / checksum_name
        try:
            checksum_line = checksum_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as exc:
            raise ReleaseError(f"missing checksum sidecar: {checksum_name}") from exc
        if checksum_line != f"{zip_sha256}  {zip_name}":
            raise ReleaseError(f"invalid checksum sidecar: {checksum_name}")

        preview_record = report.get("preview")
        preview: Optional[dict[str, str]] = None
        if preview_record is not None:
            if not isinstance(preview_record, dict):
                raise ReleaseError(f"{report_name} has an invalid preview record")
            preview_name = preview_record.get("path")
            preview_sha256 = preview_record.get("sha256")
            if not isinstance(preview_name, str) or not isinstance(preview_sha256, str):
                raise ReleaseError(f"{report_name} has an invalid preview record")
            preview_path = build_dir / preview_name
            if not preview_path.is_file():
                raise ReleaseError(f"missing preview: {preview_name}")
            _verify_checksum(preview_path, preview_sha256, preview_name)
            preview = {"path": preview_name, "sha256": preview_sha256}

        template_entries.append({
            "id": template_id,
            "status": report["status"],
            "zip": {
                "path": zip_name,
                "sha256": zip_sha256,
                "checksum": checksum_name,
            },
            "preview": preview,
            "build_report": report_name,
        })

    if len(source_epochs) != 1:
        raise ReleaseError("release reports do not share one source_date_epoch")

    catalog_snapshot = build_dir / "CATALOG.json"
    shutil.copyfile(catalog_module.CATALOG_PATH, catalog_snapshot)
    index = {
        "format_version": "1.0.0",
        "release_version": catalog["release_version"],
        "tag": tag,
        "source_commit": source_commit,
        "source_date_epoch": source_epochs.pop(),
        "catalog": {
            "path": catalog_snapshot.name,
            "sha256": sha256_file(catalog_snapshot),
        },
        "templates": template_entries,
    }
    (build_dir / "release-index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return index


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and assemble Apograph releases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tag_parser = subparsers.add_parser(
        "validate-tag", help="validate a publication tag against catalog and changelog"
    )
    tag_parser.add_argument("--tag", required=True)

    assemble_parser = subparsers.add_parser(
        "assemble", help="verify build outputs and create release metadata"
    )
    assemble_parser.add_argument("--build-dir", type=Path, required=True)
    assemble_parser.add_argument("--source-commit", required=True)
    assemble_parser.add_argument("--tag")

    args = parser.parse_args(argv)
    try:
        catalog = catalog_module.load_catalog()
        catalog_module.require_valid_catalog(catalog)
        if args.command == "validate-tag":
            version = validate_release_tag(
                catalog, args.tag, CHANGELOG_PATH.read_text(encoding="utf-8")
            )
            print(f"Release tag valid: {version}")
        elif args.command == "assemble":
            index = assemble_release_candidate(
                catalog,
                args.build_dir,
                source_commit=args.source_commit,
                tag=args.tag,
            )
            print(
                f"Release candidate assembled: {len(index['templates'])} template(s)"
            )
    except (catalog_module.CatalogValidationError, ReleaseError) as exc:
        print(f"Release validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
