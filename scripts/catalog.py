#!/usr/bin/env python3
"""Validate the Apograph catalog and generate catalog-backed documentation.

This module deliberately uses only the Python standard library. The JSON Schema
file is the portable contract for editors and external tooling; the checks below
enforce the same repository-specific invariants without adding a runtime
dependency on a JSON Schema package.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Optional, Sequence
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "CATALOG.json"
SCHEMA_PATH = REPO_ROOT / "catalog.schema.json"
README_PATH = REPO_ROOT / "README.md"

PUBLIC_STATUSES = {"beta", "stable"}
STATUSES = {"draft", "beta", "stable", "deprecated"}
FORMATS = {"latex", "typst"}
PURPOSES = {"thesis", "presentation", "report", "cv", "letter", "other"}
RELATIONSHIPS = {"generic", "unofficial", "endorsed", "official"}
COMPILERS = {"pdflatex", "lualatex", "xelatex", "typst"}
ENTRYPOINT_ROLES = {"starter", "showcase", "companion", "test"}
ASSET_MODES = {"bundled", "fetched", "user-provided", "generated", "placeholder"}
LICENSE_STATUSES = {"declared", "review-required", "verified"}
UPSTREAM_KINDS = {"original", "adapted", "redistributed"}
OVERLEAF_STATES = {"untested", "compatible", "incompatible", "not-applicable"}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?"
    r"(?:\+[0-9A-Za-z.-]+)?$"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

ROOT_FIELDS = {"$schema", "schema_version", "release_version", "repository", "templates"}
REPOSITORY_FIELDS = {"name", "url", "description", "maintainer", "tooling_license"}
TEMPLATE_FIELDS = {
    "id", "name", "description", "purpose", "variant", "format", "status",
    "institution", "compiler", "compatibility", "source_dir", "entrypoints",
    "shared_deps", "license", "upstream", "assets", "tags", "maintainers",
    "readiness_notes", "created", "updated",
}
INSTITUTION_FIELDS = {"id", "name", "relationship", "requirements_url", "last_verified"}
COMPATIBILITY_FIELDS = {"texlive", "overleaf"}
ENTRYPOINT_FIELDS = {"path", "role", "include_in_artifact", "preview"}
LICENSE_FIELDS = {"expression", "status", "notes"}
UPSTREAM_FIELDS = {"kind", "sources", "notes"}
UPSTREAM_SOURCE_FIELDS = {"title", "url", "authors", "revision", "license"}
ASSET_FIELDS = {
    "id", "description", "local_path", "mode", "required", "source_url",
    "sha256", "fallback", "license",
}
MAINTAINER_FIELDS = {"name", "github"}

PUBLIC_START = "<!-- BEGIN GENERATED:PUBLIC_TEMPLATES -->"
PUBLIC_END = "<!-- END GENERATED:PUBLIC_TEMPLATES -->"


class CatalogValidationError(Exception):
    """Raised when catalog validation reports one or more errors."""

    def __init__(self, errors: Sequence[str]):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogValidationError([f"missing file: {path.relative_to(REPO_ROOT)}"]) from exc
    except json.JSONDecodeError as exc:
        raise CatalogValidationError([
            f"invalid JSON in {path.relative_to(REPO_ROOT)}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ]) from exc
    if not isinstance(data, dict):
        raise CatalogValidationError([f"{path.relative_to(REPO_ROOT)} must contain a JSON object"])
    return data


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    return load_json(path)


def _fields(value: Any, expected: set[str], context: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{context}: expected an object")
        return False
    missing = expected - set(value)
    unknown = set(value) - expected
    for field in sorted(missing):
        errors.append(f"{context}: missing required field '{field}'")
    for field in sorted(unknown):
        errors.append(f"{context}: unknown field '{field}'")
    return not missing


def _nonempty_string(value: Any, context: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{context}: expected a non-empty string")
        return False
    return True


def _slug(value: Any, context: str, errors: list[str]) -> bool:
    if not _nonempty_string(value, context, errors):
        return False
    if not SLUG_RE.fullmatch(value):
        errors.append(f"{context}: '{value}' is not a lowercase hyphenated slug")
        return False
    return True


def _url(value: Any, context: str, errors: list[str], nullable: bool = False) -> bool:
    if value is None and nullable:
        return True
    if not _nonempty_string(value, context, errors):
        return False
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(f"{context}: expected an HTTP(S) URL")
        return False
    return True


def _date(value: Any, context: str, errors: list[str], nullable: bool = False) -> bool:
    if value is None and nullable:
        return True
    if not _nonempty_string(value, context, errors):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{context}: expected an ISO date (YYYY-MM-DD)")
        return False
    return True


def _safe_relative_path(value: Any, context: str, errors: list[str]) -> Optional[PurePosixPath]:
    if not _nonempty_string(value, context, errors):
        return None
    if "\\" in value:
        errors.append(f"{context}: use POSIX '/' separators")
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{context}: path must be relative and may not contain '..'")
        return None
    return path


def _enum(value: Any, allowed: set[str], context: str, errors: list[str]) -> bool:
    if value not in allowed:
        errors.append(f"{context}: expected one of {', '.join(sorted(allowed))}; got {value!r}")
        return False
    return True


def _validate_license(value: Any, context: str, errors: list[str]) -> None:
    if not _fields(value, LICENSE_FIELDS, context, errors):
        return
    expression = value.get("expression")
    if expression is not None:
        _nonempty_string(expression, f"{context}.expression", errors)
    _enum(value.get("status"), LICENSE_STATUSES, f"{context}.status", errors)
    if not isinstance(value.get("notes"), str):
        errors.append(f"{context}.notes: expected a string")


def _validate_institution(value: Any, context: str, errors: list[str]) -> None:
    if not _fields(value, INSTITUTION_FIELDS, context, errors):
        return
    _slug(value.get("id"), f"{context}.id", errors)
    _nonempty_string(value.get("name"), f"{context}.name", errors)
    relationship = value.get("relationship")
    _enum(relationship, RELATIONSHIPS, f"{context}.relationship", errors)
    _url(value.get("requirements_url"), f"{context}.requirements_url", errors, nullable=True)
    _date(value.get("last_verified"), f"{context}.last_verified", errors, nullable=True)
    if value.get("id") == "generic" and relationship != "generic":
        errors.append(f"{context}: the generic institution must use relationship 'generic'")
    if value.get("id") != "generic" and relationship == "generic":
        errors.append(f"{context}: a named institution may not use relationship 'generic'")


def _validate_upstream(value: Any, context: str, errors: list[str]) -> None:
    if not _fields(value, UPSTREAM_FIELDS, context, errors):
        return
    kind = value.get("kind")
    _enum(kind, UPSTREAM_KINDS, f"{context}.kind", errors)
    sources = value.get("sources")
    if not isinstance(sources, list):
        errors.append(f"{context}.sources: expected an array")
        return
    if kind in {"adapted", "redistributed"} and not sources:
        errors.append(f"{context}.sources: adapted/redistributed work requires at least one source")
    for index, source in enumerate(sources):
        source_context = f"{context}.sources[{index}]"
        if not _fields(source, UPSTREAM_SOURCE_FIELDS, source_context, errors):
            continue
        _nonempty_string(source.get("title"), f"{source_context}.title", errors)
        _url(source.get("url"), f"{source_context}.url", errors)
        authors = source.get("authors")
        if not isinstance(authors, list):
            errors.append(f"{source_context}.authors: expected an array")
        else:
            for author_index, author in enumerate(authors):
                _nonempty_string(author, f"{source_context}.authors[{author_index}]", errors)
        for optional in ("revision", "license"):
            item = source.get(optional)
            if item is not None:
                _nonempty_string(item, f"{source_context}.{optional}", errors)
    if not isinstance(value.get("notes"), str):
        errors.append(f"{context}.notes: expected a string")


def _resolve_repo_path(relative: PurePosixPath) -> Path:
    return REPO_ROOT.joinpath(*relative.parts)


def _validate_template(template: Any, index: int, ids: set[str], errors: list[str]) -> None:
    context = f"templates[{index}]"
    if not _fields(template, TEMPLATE_FIELDS, context, errors):
        return

    template_id = template.get("id")
    if _slug(template_id, f"{context}.id", errors):
        if template_id in ids:
            errors.append(f"{context}.id: duplicate template ID '{template_id}'")
        ids.add(template_id)
        context = f"template[{template_id}]"

    for field in ("name", "description", "readiness_notes"):
        _nonempty_string(template.get(field), f"{context}.{field}", errors)
    _enum(template.get("purpose"), PURPOSES, f"{context}.purpose", errors)
    _slug(template.get("variant"), f"{context}.variant", errors)
    template_format = template.get("format")
    _enum(template_format, FORMATS, f"{context}.format", errors)
    status = template.get("status")
    _enum(status, STATUSES, f"{context}.status", errors)
    _validate_institution(template.get("institution"), f"{context}.institution", errors)

    compiler = template.get("compiler")
    _enum(compiler, COMPILERS, f"{context}.compiler", errors)
    if template_format == "latex" and compiler == "typst":
        errors.append(f"{context}.compiler: a LaTeX template may not use the Typst compiler")
    if template_format == "typst" and compiler != "typst":
        errors.append(f"{context}.compiler: a Typst template must use the Typst compiler")

    compatibility = template.get("compatibility")
    if _fields(compatibility, COMPATIBILITY_FIELDS, f"{context}.compatibility", errors):
        texlive = compatibility.get("texlive")
        if not isinstance(texlive, list) or any(not isinstance(item, str) or not item for item in texlive):
            errors.append(f"{context}.compatibility.texlive: expected an array of non-empty strings")
        elif len(texlive) != len(set(texlive)):
            errors.append(f"{context}.compatibility.texlive: duplicate values are not allowed")
        _enum(compatibility.get("overleaf"), OVERLEAF_STATES, f"{context}.compatibility.overleaf", errors)
    if not isinstance(compatibility, dict):
        compatibility = {}

    source_path = _safe_relative_path(template.get("source_dir"), f"{context}.source_dir", errors)
    source_dir: Optional[Path] = None
    if source_path is not None:
        if not source_path.parts or source_path.parts[0] != "templates":
            errors.append(f"{context}.source_dir: must live below templates/")
        source_dir = _resolve_repo_path(source_path)
        if not source_dir.is_dir():
            errors.append(f"{context}.source_dir: directory does not exist: {source_path}")

    entrypoints = template.get("entrypoints")
    starter_count = 0
    preview_count = 0
    entrypoint_paths: set[str] = set()
    if not isinstance(entrypoints, list) or not entrypoints:
        errors.append(f"{context}.entrypoints: expected a non-empty array")
    else:
        for entry_index, entrypoint in enumerate(entrypoints):
            entry_context = f"{context}.entrypoints[{entry_index}]"
            if not _fields(entrypoint, ENTRYPOINT_FIELDS, entry_context, errors):
                continue
            path = _safe_relative_path(entrypoint.get("path"), f"{entry_context}.path", errors)
            role = entrypoint.get("role")
            _enum(role, ENTRYPOINT_ROLES, f"{entry_context}.role", errors)
            if role == "starter":
                starter_count += 1
            for boolean_field in ("include_in_artifact", "preview"):
                if not isinstance(entrypoint.get(boolean_field), bool):
                    errors.append(f"{entry_context}.{boolean_field}: expected a boolean")
            if entrypoint.get("preview"):
                preview_count += 1
            if path is not None:
                path_string = path.as_posix()
                if path_string in entrypoint_paths:
                    errors.append(f"{entry_context}.path: duplicate entry point '{path_string}'")
                entrypoint_paths.add(path_string)
                if source_dir is not None and not (source_dir / Path(*path.parts)).is_file():
                    errors.append(f"{entry_context}.path: file does not exist below source_dir: {path_string}")

    shared_deps = template.get("shared_deps")
    if not isinstance(shared_deps, list):
        errors.append(f"{context}.shared_deps: expected an array")
    else:
        if all(isinstance(item, str) for item in shared_deps) and len(shared_deps) != len(set(shared_deps)):
            errors.append(f"{context}.shared_deps: duplicate paths are not allowed")
        for dep_index, dependency in enumerate(shared_deps):
            dep_context = f"{context}.shared_deps[{dep_index}]"
            path = _safe_relative_path(dependency, dep_context, errors)
            if path is not None:
                if not path.parts or path.parts[0] != "shared":
                    errors.append(f"{dep_context}: shared dependency must live below shared/")
                if not _resolve_repo_path(path).is_file():
                    errors.append(f"{dep_context}: file does not exist: {path}")

    license_data = template.get("license")
    _validate_license(license_data, f"{context}.license", errors)
    _validate_upstream(template.get("upstream"), f"{context}.upstream", errors)

    assets = template.get("assets")
    asset_ids: set[str] = set()
    if not isinstance(assets, list):
        errors.append(f"{context}.assets: expected an array")
    else:
        for asset_index, asset in enumerate(assets):
            asset_context = f"{context}.assets[{asset_index}]"
            if not _fields(asset, ASSET_FIELDS, asset_context, errors):
                continue
            asset_id = asset.get("id")
            if _slug(asset_id, f"{asset_context}.id", errors):
                if asset_id in asset_ids:
                    errors.append(f"{asset_context}.id: duplicate asset ID '{asset_id}'")
                asset_ids.add(asset_id)
            _nonempty_string(asset.get("description"), f"{asset_context}.description", errors)
            local_path = _safe_relative_path(asset.get("local_path"), f"{asset_context}.local_path", errors)
            mode = asset.get("mode")
            _enum(mode, ASSET_MODES, f"{asset_context}.mode", errors)
            if not isinstance(asset.get("required"), bool):
                errors.append(f"{asset_context}.required: expected a boolean")
            _url(asset.get("source_url"), f"{asset_context}.source_url", errors, nullable=True)
            sha256 = asset.get("sha256")
            if sha256 is not None and (not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256)):
                errors.append(f"{asset_context}.sha256: expected 64 lowercase hexadecimal characters")
            fallback = asset.get("fallback")
            if fallback is not None:
                _nonempty_string(fallback, f"{asset_context}.fallback", errors)
            _validate_license(asset.get("license"), f"{asset_context}.license", errors)

            if mode == "bundled" and source_dir is not None and local_path is not None:
                if not (source_dir / Path(*local_path.parts)).is_file():
                    errors.append(f"{asset_context}: bundled asset does not exist: {local_path}")
            if mode == "fetched":
                if asset.get("source_url") is None:
                    errors.append(f"{asset_context}: fetched assets require source_url")
                if asset.get("sha256") is None:
                    errors.append(f"{asset_context}: fetched assets require sha256")
            if mode == "user-provided" and asset.get("required") is False and not fallback:
                errors.append(f"{asset_context}: optional user-provided assets require a fallback")

    tags = template.get("tags")
    if not isinstance(tags, list) or not tags:
        errors.append(f"{context}.tags: expected a non-empty array")
    else:
        if all(isinstance(item, str) for item in tags) and len(tags) != len(set(tags)):
            errors.append(f"{context}.tags: duplicate tags are not allowed")
        for tag_index, tag in enumerate(tags):
            _slug(tag, f"{context}.tags[{tag_index}]", errors)

    maintainers = template.get("maintainers")
    if not isinstance(maintainers, list) or not maintainers:
        errors.append(f"{context}.maintainers: expected a non-empty array")
    else:
        for maintainer_index, maintainer in enumerate(maintainers):
            maintainer_context = f"{context}.maintainers[{maintainer_index}]"
            if not _fields(maintainer, MAINTAINER_FIELDS, maintainer_context, errors):
                continue
            _nonempty_string(maintainer.get("name"), f"{maintainer_context}.name", errors)
            github = maintainer.get("github")
            if github is not None:
                _nonempty_string(github, f"{maintainer_context}.github", errors)

    _date(template.get("created"), f"{context}.created", errors)
    _date(template.get("updated"), f"{context}.updated", errors)

    if status in PUBLIC_STATUSES:
        if starter_count != 1:
            errors.append(f"{context}: beta/stable templates require exactly one starter entry point")
        if not isinstance(license_data, dict) or license_data.get("status") != "verified" or not license_data.get("expression"):
            errors.append(f"{context}: beta/stable templates require a verified license expression")
        if template_format == "latex" and compatibility.get("overleaf") == "untested":
            errors.append(f"{context}: beta/stable LaTeX templates require an explicit Overleaf compatibility result")
    if status == "stable":
        if preview_count < 1:
            errors.append(f"{context}: stable templates require a preview entry point")
        if not compatibility.get("texlive") and template_format == "latex":
            errors.append(f"{context}: stable LaTeX templates require at least one tested TeX Live version")


def validate_catalog(catalog: dict[str, Any], check_repository: bool = True) -> list[str]:
    """Return a list of validation errors; an empty list means valid."""
    errors: list[str] = []

    if check_repository:
        try:
            schema = load_json(SCHEMA_PATH)
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append("catalog.schema.json: expected JSON Schema draft 2020-12")
        except CatalogValidationError as exc:
            errors.extend(exc.errors)

    if not _fields(catalog, ROOT_FIELDS, "catalog", errors):
        return errors
    if catalog.get("$schema") != "./catalog.schema.json":
        errors.append("catalog.$schema: expected './catalog.schema.json'")
    for field in ("schema_version", "release_version"):
        value = catalog.get(field)
        if not isinstance(value, str) or not SEMVER_RE.fullmatch(value):
            errors.append(f"catalog.{field}: expected a semantic version")

    repository = catalog.get("repository")
    if _fields(repository, REPOSITORY_FIELDS, "catalog.repository", errors):
        for field in ("name", "description", "maintainer", "tooling_license"):
            _nonempty_string(repository.get(field), f"catalog.repository.{field}", errors)
        _url(repository.get("url"), "catalog.repository.url", errors)

    templates = catalog.get("templates")
    if not isinstance(templates, list):
        errors.append("catalog.templates: expected an array")
        return errors

    ids: set[str] = set()
    for index, template in enumerate(templates):
        _validate_template(template, index, ids, errors)

    if check_repository:
        duplicate_manifests = sorted(REPO_ROOT.glob("templates/*/*/*/template.json"))
        for path in duplicate_manifests:
            errors.append(
                f"repository: remove duplicate source manifest {path.relative_to(REPO_ROOT)}; "
                "template.json is generated into artifacts"
            )

    return errors


def require_valid_catalog(catalog: dict[str, Any], check_repository: bool = True) -> None:
    errors = validate_catalog(catalog, check_repository=check_repository)
    if errors:
        raise CatalogValidationError(errors)


def select_entrypoint(template: dict[str, Any], preview: bool = False) -> dict[str, Any]:
    """Select the current preview/starter entry point for legacy scripts."""
    entrypoints = template.get("entrypoints", [])
    if preview:
        for entrypoint in entrypoints:
            if entrypoint.get("preview"):
                return entrypoint
    for preferred_role in ("starter", "showcase", "companion"):
        for entrypoint in entrypoints:
            if entrypoint.get("role") == preferred_role:
                return entrypoint
    if entrypoints:
        return entrypoints[0]
    legacy = template.get("main_file")
    if legacy:
        return {"path": legacy, "role": "starter", "include_in_artifact": True, "preview": False}
    return {"path": "main.tex" if template.get("format") == "latex" else "main.typ"}


def public_templates(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        (template for template in catalog.get("templates", []) if template.get("status") in PUBLIC_STATUSES),
        key=lambda template: (template.get("purpose", ""), template.get("name", "")),
    )


def _escape_table(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_public_listing(catalog: dict[str, Any]) -> str:
    public = public_templates(catalog)
    drafts = sorted(
        (template for template in catalog.get("templates", []) if template.get("status") == "draft"),
        key=lambda template: (template.get("purpose", ""), template.get("name", "")),
    )
    lines = [PUBLIC_START, ""]
    if public:
        lines.extend([
            "| Template | Purpose | Institution | Format | Status | ID |",
            "|---|---|---|---|---|---|",
        ])
        for template in public:
            institution = template["institution"]
            lines.append(
                "| {name} | {purpose} | {institution} ({relationship}) | {format} | {status} | `{id}` |".format(
                    name=_escape_table(template["name"]),
                    purpose=_escape_table(template["purpose"]),
                    institution=_escape_table(institution["name"]),
                    relationship=_escape_table(institution["relationship"]),
                    format=_escape_table(template["format"]),
                    status=_escape_table(template["status"]),
                    id=_escape_table(template["id"]),
                )
            )
    else:
        lines.extend([
            "No template is currently eligible for public download. The repository is in",
            "pre-release development; entries remain drafts until their licensing, artifact,",
            "documentation, and compatibility gates pass.",
        ])

    if drafts:
        lines.extend([
            "",
            "<details>",
            "<summary>Draft inventory (not release-ready)</summary>",
            "",
            "| Draft | Purpose | Institution | Format | ID |",
            "|---|---|---|---|---|",
        ])
        for template in drafts:
            lines.append(
                "| {name} | {purpose} | {institution} | {format} | `{id}` |".format(
                    name=_escape_table(template["name"]),
                    purpose=_escape_table(template["purpose"]),
                    institution=_escape_table(template["institution"]["name"]),
                    format=_escape_table(template["format"]),
                    id=_escape_table(template["id"]),
                )
            )
        lines.extend(["", "</details>"])
    lines.extend(["", PUBLIC_END])
    return "\n".join(lines)


def generated_readme(catalog: dict[str, Any], readme_text: str) -> str:
    if PUBLIC_START not in readme_text or PUBLIC_END not in readme_text:
        raise CatalogValidationError([
            f"README.md must contain {PUBLIC_START!r} and {PUBLIC_END!r} markers"
        ])
    before, remainder = readme_text.split(PUBLIC_START, 1)
    _, after = remainder.split(PUBLIC_END, 1)
    return before + render_public_listing(catalog) + after


def generate_readme(catalog: dict[str, Any], check: bool = False) -> bool:
    current = README_PATH.read_text(encoding="utf-8")
    generated = generated_readme(catalog, current)
    if current == generated:
        return False
    if check:
        raise CatalogValidationError([
            "README.md catalog listing is stale; run: python3 scripts/catalog.py generate-readme"
        ])
    README_PATH.write_text(generated, encoding="utf-8")
    return True


def print_templates(catalog: dict[str, Any], statuses: Optional[Iterable[str]] = None) -> None:
    selected_statuses = set(statuses or STATUSES)
    templates = [
        template for template in catalog.get("templates", [])
        if template.get("status") in selected_statuses
    ]
    for template in sorted(templates, key=lambda item: item["id"]):
        print(f"{template['id']:45s} {template['status']:10s} {template['name']}")


def _print_errors(errors: Sequence[str]) -> None:
    print(f"Catalog validation failed with {len(errors)} error(s):", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render the Apograph catalog.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate catalog data and repository paths")

    generate_parser = subparsers.add_parser(
        "generate-readme", help="regenerate the README template listing"
    )
    generate_parser.add_argument(
        "--check", action="store_true", help="fail instead of writing when the listing is stale"
    )

    list_parser = subparsers.add_parser("list", help="list catalog entries")
    list_parser.add_argument(
        "--status", action="append", choices=sorted(STATUSES), help="filter by status (repeatable)"
    )

    args = parser.parse_args(argv)
    try:
        catalog = load_catalog()
        require_valid_catalog(catalog)
        if args.command == "validate":
            print(f"Catalog valid: {len(catalog['templates'])} template(s)")
        elif args.command == "generate-readme":
            changed = generate_readme(catalog, check=args.check)
            if not args.check:
                print("README template listing updated" if changed else "README template listing already current")
        elif args.command == "list":
            print_templates(catalog, statuses=args.status)
    except CatalogValidationError as exc:
        _print_errors(exc.errors)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
