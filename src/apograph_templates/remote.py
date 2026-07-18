"""Resolve and verify template artifacts from published GitHub Releases."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from . import PRODUCT_NAME, __version__
from .errors import ApographError


DEFAULT_REPOSITORY = "eliainnocenti/apograph"
DEFAULT_API_URL = "https://api.github.com"
API_VERSION = "2026-03-10"
INDEX_NAME = "release-index.json"
MAX_METADATA_BYTES = 10 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
TEMPLATE_ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PUBLIC_STATUSES = {"beta", "stable"}


@dataclass(frozen=True)
class ReleaseAsset:
    """One downloadable asset attached to a GitHub Release."""

    name: str
    url: str
    digest: str | None = None


@dataclass(frozen=True)
class ResolvedRelease:
    """A release whose index and catalog snapshot have been verified."""

    tag: str
    html_url: str
    assets: dict[str, ReleaseAsset]
    index: dict[str, Any]
    catalog: dict[str, Any]


class GitHubHTTPClient:
    """Small authenticated-or-anonymous HTTP client for public GitHub data."""

    def __init__(self, *, token: str | None = None, timeout: float = 30.0) -> None:
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout

    def _request(self, url: str) -> Request:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{PRODUCT_NAME}/{__version__}",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return Request(url, headers=headers)

    def read_bytes(self, url: str, *, limit: int = MAX_METADATA_BYTES) -> bytes:
        try:
            with urlopen(self._request(url), timeout=self.timeout) as response:
                data = response.read(limit + 1)
        except HTTPError as exc:
            if exc.code == 404:
                raise ApographError(f"GitHub resource not found: {url}") from exc
            if exc.code == 403:
                raise ApographError(
                    "GitHub refused the request or its anonymous API limit was reached; "
                    "try again later or set GITHUB_TOKEN"
                ) from exc
            raise ApographError(f"GitHub request failed with HTTP {exc.code}: {url}") from exc
        except URLError as exc:
            raise ApographError(f"Could not reach GitHub: {exc.reason}") from exc

        if len(data) > limit:
            raise ApographError(f"GitHub metadata exceeds the {limit}-byte safety limit")
        return data

    def read_json(self, url: str) -> Any:
        data = self.read_bytes(url)
        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApographError(f"GitHub returned invalid JSON: {url}") from exc

    def download(self, url: str, destination: Path) -> str:
        digest = hashlib.sha256()
        try:
            with urlopen(self._request(url), timeout=self.timeout) as response:
                with destination.open("wb") as output:
                    while chunk := response.read(1024 * 1024):
                        digest.update(chunk)
                        output.write(chunk)
        except HTTPError as exc:
            destination.unlink(missing_ok=True)
            raise ApographError(
                f"Artifact download failed with HTTP {exc.code}: {url}"
            ) from exc
        except URLError as exc:
            destination.unlink(missing_ok=True)
            raise ApographError(f"Could not download the artifact: {exc.reason}") from exc
        except OSError as exc:
            destination.unlink(missing_ok=True)
            raise ApographError(f"Could not write the downloaded artifact: {exc}") from exc
        return digest.hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ApographError(f"Invalid {context}: expected an object")
    return value


def _require_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ApographError(f"Invalid {context}: expected a non-empty string")
    return value


def _require_sha256(value: Any, context: str) -> str:
    digest = _require_string(value, context)
    if SHA256_RE.fullmatch(digest) is None:
        raise ApographError(f"Invalid {context}: expected a SHA-256 digest")
    return digest


def _require_https_url(value: Any, context: str) -> str:
    url = _require_string(value, context)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username is not None:
        raise ApographError(f"Invalid {context}: expected an HTTPS URL")
    return url


def _require_template_id(value: Any, context: str = "template ID") -> str:
    template_id = _require_string(value, context)
    if TEMPLATE_ID_RE.fullmatch(template_id) is None:
        raise ApographError(f"Invalid {context}: expected a lowercase slug")
    return template_id


def normalize_tag(version: str) -> str:
    """Accept either ``0.2.0`` or ``v0.2.0`` and return a release tag."""
    normalized = version.strip()
    if not normalized:
        raise ApographError("Release version may not be empty")
    return normalized if normalized.startswith("v") else f"v{normalized}"


class GitHubReleaseSource:
    """Catalog-backed access to Apograph's immutable release artifacts."""

    def __init__(
        self,
        repository: str = DEFAULT_REPOSITORY,
        *,
        api_url: str = DEFAULT_API_URL,
        http: GitHubHTTPClient | None = None,
    ) -> None:
        parts = repository.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("repository must use the form OWNER/NAME")
        self.owner, self.repository = parts
        self.api_url = api_url.rstrip("/")
        self.http = http or GitHubHTTPClient()

    def _api(self, path: str) -> str:
        owner = quote(self.owner, safe="")
        repository = quote(self.repository, safe="")
        return f"{self.api_url}/repos/{owner}/{repository}{path}"

    def _release_metadata(self, version: str | None) -> dict[str, Any]:
        if version is not None:
            tag = quote(normalize_tag(version), safe="")
            return _require_object(
                self.http.read_json(self._api(f"/releases/tags/{tag}")),
                "GitHub release",
            )

        releases = self.http.read_json(self._api("/releases?per_page=100"))
        if not isinstance(releases, list):
            raise ApographError("Invalid GitHub releases response: expected an array")
        published = [
            release
            for release in releases
            if isinstance(release, dict)
            and release.get("draft") is False
            and isinstance(release.get("published_at"), str)
        ]
        if not published:
            raise ApographError("Apograph has no published releases")
        return max(published, key=lambda release: release["published_at"])

    @staticmethod
    def _assets(release: dict[str, Any]) -> dict[str, ReleaseAsset]:
        raw_assets = release.get("assets")
        if not isinstance(raw_assets, list):
            raise ApographError("Invalid GitHub release: assets must be an array")
        assets: dict[str, ReleaseAsset] = {}
        for raw_asset in raw_assets:
            asset = _require_object(raw_asset, "GitHub release asset")
            if asset.get("state") != "uploaded":
                continue
            name = _require_string(asset.get("name"), "release asset name")
            url = _require_https_url(
                asset.get("browser_download_url"), f"release asset {name} URL"
            )
            if name in assets:
                raise ApographError(f"GitHub release contains duplicate asset: {name}")
            raw_digest = asset.get("digest")
            digest = None
            if raw_digest is not None:
                if not isinstance(raw_digest, str) or not raw_digest.startswith("sha256:"):
                    raise ApographError(f"Unsupported GitHub digest for release asset: {name}")
                digest = _require_sha256(raw_digest.removeprefix("sha256:"), f"{name} digest")
            assets[name] = ReleaseAsset(name=name, url=url, digest=digest)
        return assets

    def _read_asset(self, assets: dict[str, ReleaseAsset], name: str) -> bytes:
        try:
            asset = assets[name]
        except KeyError as exc:
            raise ApographError(f"Published release is missing required asset: {name}") from exc
        data = self.http.read_bytes(asset.url)
        if asset.digest is not None and _sha256(data) != asset.digest:
            raise ApographError(f"GitHub digest mismatch for release asset: {name}")
        return data

    @staticmethod
    def _parse_json(data: bytes, context: str) -> dict[str, Any]:
        try:
            value = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApographError(f"Invalid {context}: expected UTF-8 JSON") from exc
        return _require_object(value, context)

    @staticmethod
    def _validate_index(
        index: dict[str, Any], tag: str, assets: dict[str, ReleaseAsset]
    ) -> None:
        if index.get("format_version") != "1.0.0":
            raise ApographError("Unsupported release-index format_version")
        if index.get("tag") != tag:
            raise ApographError("Release index tag does not match the GitHub Release")
        release_version = _require_string(
            index.get("release_version"), "release-index release_version"
        )
        if tag != f"v{release_version}":
            raise ApographError("Release index version does not match its tag")

        catalog = _require_object(index.get("catalog"), "release-index catalog")
        catalog_name = _require_string(catalog.get("path"), "catalog asset path")
        _require_sha256(catalog.get("sha256"), "catalog SHA-256")
        if catalog_name not in assets:
            raise ApographError(f"Published release is missing required asset: {catalog_name}")

        raw_templates = index.get("templates")
        if not isinstance(raw_templates, list) or not raw_templates:
            raise ApographError("Release index contains no templates")
        seen: set[str] = set()
        for raw_template in raw_templates:
            template = _require_object(raw_template, "release-index template")
            template_id = _require_template_id(template.get("id"))
            if template_id in seen:
                raise ApographError(f"Release index contains duplicate template: {template_id}")
            seen.add(template_id)
            zip_record = _require_object(template.get("zip"), f"{template_id} ZIP record")
            zip_name = _require_string(zip_record.get("path"), f"{template_id} ZIP path")
            _require_sha256(zip_record.get("sha256"), f"{template_id} ZIP SHA-256")
            if zip_name not in assets:
                raise ApographError(f"Published release is missing required asset: {zip_name}")

    @staticmethod
    def _validate_catalog(index: dict[str, Any], catalog: dict[str, Any]) -> None:
        if catalog.get("release_version") != index.get("release_version"):
            raise ApographError("Catalog release_version does not match the release index")
        raw_catalog_templates = catalog.get("templates")
        if not isinstance(raw_catalog_templates, list):
            raise ApographError("Invalid catalog snapshot: templates must be an array")
        public_ids: set[str] = set()
        for raw_template in raw_catalog_templates:
            if not isinstance(raw_template, dict) or raw_template.get("status") not in PUBLIC_STATUSES:
                continue
            template_id = _require_template_id(raw_template.get("id"))
            if template_id in public_ids:
                raise ApographError(f"Catalog contains duplicate template: {template_id}")
            public_ids.add(template_id)
            for field in ("name", "description", "purpose", "format", "compiler"):
                _require_string(raw_template.get(field), f"{template_id} catalog {field}")
            institution = _require_object(
                raw_template.get("institution"), f"{template_id} catalog institution"
            )
            _require_string(
                institution.get("name"), f"{template_id} institution name"
            )
            _require_string(
                institution.get("relationship"),
                f"{template_id} institution relationship",
            )
            license_data = _require_object(
                raw_template.get("license"), f"{template_id} catalog license"
            )
            _require_string(
                license_data.get("expression"), f"{template_id} license expression"
            )
        index_ids = {
            _require_template_id(template.get("id"))
            for template in index["templates"]
            if isinstance(template, dict)
        }
        if public_ids != index_ids:
            raise ApographError("Release index templates do not match the public catalog")

    def resolve(self, version: str | None = None) -> ResolvedRelease:
        """Resolve the newest published release, or one exact requested tag."""
        release = self._release_metadata(version)
        tag = _require_string(release.get("tag_name"), "GitHub release tag")
        html_url = _require_https_url(release.get("html_url"), "GitHub release URL")
        assets = self._assets(release)
        index = self._parse_json(self._read_asset(assets, INDEX_NAME), "release index")
        self._validate_index(index, tag, assets)

        catalog_record = _require_object(index["catalog"], "release-index catalog")
        catalog_name = _require_string(catalog_record.get("path"), "catalog asset path")
        catalog_bytes = self._read_asset(assets, catalog_name)
        expected_catalog_sha = _require_sha256(
            catalog_record.get("sha256"), "catalog SHA-256"
        )
        if _sha256(catalog_bytes) != expected_catalog_sha:
            raise ApographError("Catalog snapshot checksum does not match the release index")
        catalog = self._parse_json(catalog_bytes, "catalog snapshot")
        self._validate_catalog(index, catalog)
        return ResolvedRelease(
            tag=tag,
            html_url=html_url,
            assets=assets,
            index=index,
            catalog=catalog,
        )

    @staticmethod
    def index_template(release: ResolvedRelease, template_id: str) -> dict[str, Any]:
        for raw_template in release.index["templates"]:
            if isinstance(raw_template, dict) and raw_template.get("id") == template_id:
                return raw_template
        raise ApographError(f"Template is not available in {release.tag}: {template_id}")

    def download_template(
        self, release: ResolvedRelease, template_id: str, destination: Path
    ) -> None:
        """Download one template ZIP and verify its release-index digest."""
        template = self.index_template(release, template_id)
        zip_record = _require_object(template.get("zip"), f"{template_id} ZIP record")
        zip_name = _require_string(zip_record.get("path"), f"{template_id} ZIP path")
        expected = _require_sha256(zip_record.get("sha256"), f"{template_id} ZIP SHA-256")
        asset = release.assets[zip_name]
        actual = self.http.download(asset.url, destination)
        if actual != expected:
            destination.unlink(missing_ok=True)
            raise ApographError(f"Template ZIP checksum mismatch: {zip_name}")


def catalog_templates(release: ResolvedRelease) -> list[dict[str, Any]]:
    """Return the release's public catalog records in deterministic order."""
    index_ids = {
        item["id"] for item in release.index["templates"] if isinstance(item, dict)
    }
    templates = [
        template
        for template in release.catalog["templates"]
        if isinstance(template, dict) and template.get("id") in index_ids
    ]
    return sorted(templates, key=lambda template: template["id"])


def catalog_template(release: ResolvedRelease, template_id: str) -> dict[str, Any]:
    """Find one public catalog record in a resolved release."""
    for template in catalog_templates(release):
        if template.get("id") == template_id:
            return template
    raise ApographError(f"Template is not available in {release.tag}: {template_id}")
