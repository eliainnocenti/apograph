"""Safely and atomically install one verified template archive."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

from .errors import ApographError
from .remote import GitHubReleaseSource, ResolvedRelease


MAX_ZIP_ENTRIES = 10_000
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024


def _archive_parts(filename: str) -> tuple[str, ...]:
    if not filename or "\x00" in filename or "\\" in filename:
        raise ApographError(f"Unsafe ZIP member path: {filename!r}")
    if filename.startswith("/"):
        raise ApographError(f"Unsafe ZIP member path: {filename!r}")
    raw_parts = filename.rstrip("/").split("/")
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        raise ApographError(f"Unsafe ZIP member path: {filename!r}")
    path = PurePosixPath(*raw_parts)
    if path.is_absolute() or ".." in path.parts:
        raise ApographError(f"Unsafe ZIP member path: {filename!r}")
    return tuple(path.parts)


def _validate_member_type(info: zipfile.ZipInfo) -> None:
    if info.flag_bits & 0x1:
        raise ApographError(f"Encrypted ZIP members are not supported: {info.filename}")
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode == 0:
        return
    file_type = stat.S_IFMT(mode)
    if file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
        raise ApographError(f"ZIP contains a link or special file: {info.filename}")


def safe_extract_zip(archive: Path, destination: Path) -> None:
    """Extract regular files only, rejecting traversal, links, and ZIP bombs."""
    try:
        with zipfile.ZipFile(archive) as zipped:
            members = zipped.infolist()
            if len(members) > MAX_ZIP_ENTRIES:
                raise ApographError("Template ZIP contains too many entries")
            total_size = sum(member.file_size for member in members)
            if total_size > MAX_UNCOMPRESSED_BYTES:
                raise ApographError("Template ZIP is too large after extraction")

            seen: set[tuple[str, ...]] = set()
            for member in members:
                parts = _archive_parts(member.filename)
                _validate_member_type(member)
                if parts in seen:
                    raise ApographError(f"Template ZIP contains duplicate path: {member.filename}")
                seen.add(parts)
                target = destination.joinpath(*parts)
                if member.is_dir():
                    if target.exists() and not target.is_dir():
                        raise ApographError(
                            f"Template ZIP path changes type: {member.filename}"
                        )
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
    except zipfile.BadZipFile as exc:
        raise ApographError("Downloaded template is not a valid ZIP archive") from exc
    except OSError as exc:
        raise ApographError(f"Could not extract the template ZIP: {exc}") from exc


def install_template(
    source: GitHubReleaseSource,
    release: ResolvedRelease,
    template_id: str,
    destination: Path,
) -> Path:
    """Download, verify, stage, and atomically publish one template directory."""
    target = destination.expanduser().absolute()
    if os.path.lexists(target):
        raise ApographError(
            f"Destination already exists: {destination}. Choose a new path; "
            "Apograph never overwrites existing work."
        )
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_root = Path(
            tempfile.mkdtemp(prefix=f".{target.name}.apograph-", dir=target.parent)
        )
    except OSError as exc:
        raise ApographError(f"Could not prepare destination {destination}: {exc}") from exc

    try:
        archive = temporary_root / "template.zip"
        staged = temporary_root / "template"
        staged.mkdir()
        source.download_template(release, template_id, archive)
        safe_extract_zip(archive, staged)
        os.replace(staged, target)
    except OSError as exc:
        raise ApographError(f"Could not publish template destination: {exc}") from exc
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
    return target
