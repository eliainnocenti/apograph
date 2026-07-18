#!/usr/bin/env python3
"""Validate and assemble Apograph release-candidate metadata."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

try:
    from . import catalog as catalog_module
    from .apograph.artifacts import sha256_file
except ImportError:  # Direct execution from scripts/.
    import catalog as catalog_module
    from apograph.artifacts import sha256_file


REPO_ROOT = Path(__file__).resolve().parent.parent


class ReleaseError(RuntimeError):
    """Raised when release-candidate evidence is incomplete or inconsistent."""


def release_notes_path(catalog: dict[str, Any]) -> Path:
    """Return the catalog-versioned release-notes path used by GitHub."""
    return catalog_module.release_notes_path(catalog)


def load_release_notes(catalog: dict[str, Any]) -> str:
    """Load and validate the single authored release narrative."""
    relative_path = release_notes_path(catalog)
    absolute_path = REPO_ROOT / relative_path
    try:
        notes = absolute_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ReleaseError(f"missing release notes: {relative_path}") from exc
    validate_release_notes(catalog, notes)
    return notes


def validate_release_notes(catalog: dict[str, Any], release_notes: str) -> None:
    """Require a top-level heading for the catalog release version."""
    version = catalog["release_version"]
    if not catalog_module.release_notes_heading_matches(catalog, release_notes):
        raise ReleaseError(
            f"{release_notes_path(catalog)} has no '# Apograph v{version}' heading"
        )


def validate_release_tag(catalog: dict[str, Any], tag: str, release_notes: str) -> str:
    """Validate a publication tag and its versioned release notes."""
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
    validate_release_notes(catalog, release_notes)
    return version


def validate_protected_ref(value: str) -> None:
    """Reject publication from a tag without an active GitHub protection rule."""
    if value.lower() != "true":
        raise ReleaseError(
            "publication tag is not protected; configure an active v* tag ruleset"
        )


def render_github_outputs(catalog: dict[str, Any]) -> str:
    """Render release metadata for a GitHub Actions output file."""
    load_release_notes(catalog)
    version = catalog["release_version"]
    return "\n".join(
        [
            f"release_version={version}",
            f"release_tag=v{version}",
            f"release_name=Apograph v{version}",
            f"prerelease={'true' if catalog['release_channel'] == 'prerelease' else 'false'}",
            f"release_notes_path={release_notes_path(catalog).as_posix()}",
        ]
    )


def expected_release_asset_names(catalog: dict[str, Any]) -> set[str]:
    """Return the complete public collection asset set for one release."""
    names = {"CATALOG.json", "release-index.json"}
    for template in catalog_module.public_templates(catalog):
        template_id = template["id"]
        names.update(
            {
                f"{template_id}.zip",
                f"{template_id}.zip.sha256",
                f"{template_id}.build.json",
            }
        )
        if catalog_module.template_release_urls(catalog, template)["preview"]:
            names.add(f"{template_id}.preview.pdf")
    return names


def _repository_slug(catalog: dict[str, Any]) -> str:
    parsed = urlparse(catalog["repository"]["url"])
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower() != "github.com" or len(parts) != 2:
        raise ReleaseError("catalog repository URL is not a canonical GitHub repository")
    return "/".join(parts)


def verify_published_release(
    catalog: dict[str, Any],
    tag: str,
    *,
    token: Optional[str] = None,
) -> str:
    """Verify the published GitHub Release and its exact asset/link set."""
    repository = _repository_slug(catalog)
    api_url = (
        f"https://api.github.com/repos/{repository}/releases/tags/"
        f"{quote(tag, safe='')}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "apograph-release-verifier/1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(api_url, headers=headers), timeout=30) as response:
            release = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"could not read published GitHub Release: {exc}") from exc
    if not isinstance(release, dict):
        raise ReleaseError("GitHub Release response is not an object")
    if release.get("tag_name") != tag:
        raise ReleaseError("published GitHub Release tag does not match")
    if release.get("draft") is not False:
        raise ReleaseError("published GitHub Release is still a draft")
    expected_prerelease = catalog["release_channel"] == "prerelease"
    if release.get("prerelease") is not expected_prerelease:
        raise ReleaseError("published GitHub Release channel does not match catalog")

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ReleaseError("published GitHub Release has no asset list")
    assets_by_name = {
        asset.get("name"): asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("name"), str)
    }
    expected_names = expected_release_asset_names(catalog)
    actual_names = set(assets_by_name)
    if actual_names != expected_names:
        missing = sorted(expected_names - actual_names)
        unexpected = sorted(actual_names - expected_names)
        details = []
        if missing:
            details.append(f"missing assets: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected assets: {', '.join(unexpected)}")
        raise ReleaseError("published release asset set mismatch; " + "; ".join(details))
    for name, asset in assets_by_name.items():
        if asset.get("state") != "uploaded":
            raise ReleaseError(f"published release asset is not uploaded: {name}")
        expected_url = catalog_module.release_asset_url(catalog, name)
        if asset.get("browser_download_url") != expected_url:
            raise ReleaseError(f"published release URL mismatch: {name}")
    html_url = release.get("html_url")
    if not isinstance(html_url, str) or not html_url:
        raise ReleaseError("published GitHub Release has no public URL")
    return html_url


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
        "release_channel": catalog["release_channel"],
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
    actual_files = {path.name for path in build_dir.iterdir() if path.is_file()}
    expected_files = expected_release_asset_names(catalog)
    if actual_files != expected_files:
        raise ReleaseError("assembled release file set does not match catalog")
    return index


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and assemble Apograph releases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tag_parser = subparsers.add_parser(
        "validate-tag", help="validate a publication tag against versioned release notes"
    )
    tag_parser.add_argument("--tag", required=True)
    tag_parser.add_argument("--ref-protected", required=True)

    assemble_parser = subparsers.add_parser(
        "assemble", help="verify build outputs and create release metadata"
    )
    assemble_parser.add_argument("--build-dir", type=Path, required=True)
    assemble_parser.add_argument("--source-commit", required=True)
    assemble_parser.add_argument("--tag")

    subparsers.add_parser(
        "github-output", help="emit catalog-backed GitHub Release metadata"
    )

    verify_parser = subparsers.add_parser(
        "verify-published", help="verify a published GitHub Release and its assets"
    )
    verify_parser.add_argument("--tag", required=True)

    args = parser.parse_args(argv)
    try:
        catalog = catalog_module.load_catalog()
        catalog_module.require_valid_catalog(catalog)
        release_notes = load_release_notes(catalog)
        if args.command == "validate-tag":
            version = validate_release_tag(catalog, args.tag, release_notes)
            validate_protected_ref(args.ref_protected)
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
        elif args.command == "github-output":
            print(render_github_outputs(catalog))
        elif args.command == "verify-published":
            validate_release_tag(catalog, args.tag, release_notes)
            url = verify_published_release(
                catalog, args.tag, token=os.environ.get("GITHUB_TOKEN")
            )
            print(f"Published release verified: {url}")
    except (catalog_module.CatalogValidationError, ReleaseError) as exc:
        print(f"Release validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
