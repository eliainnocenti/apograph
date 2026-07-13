"""Deterministic, self-contained Apograph artifact construction."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional

from .compile import CompilationError, CompilationResult, compile_entrypoints, copy_preview


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIRECTORIES = {
    ".git",
    ".apograph-build",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
    "venv",
}
GENERATED_FILENAMES = {".DS_Store", "preview.pdf", "template.json"}
GENERATED_SUFFIXES = {
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".dvi",
    ".fdb_latexmk",
    ".fls",
    ".glg",
    ".glo",
    ".gls",
    ".idx",
    ".ilg",
    ".ind",
    ".ist",
    ".latexmain",
    ".lof",
    ".log",
    ".lot",
    ".maf",
    ".nav",
    ".out",
    ".ps",
    ".run.xml",
    ".snm",
    ".synctex.gz",
    ".toc",
    ".vrb",
    ".xdv",
}
FIXED_EPOCH = 315532800  # 1980-01-01, the earliest ZIP timestamp.


class ArtifactError(RuntimeError):
    """Raised when a safe, self-contained artifact cannot be produced."""

    def __init__(self, message: str, *, debug_dir: Optional[Path] = None):
        super().__init__(message)
        self.debug_dir = debug_dir


@dataclass(frozen=True)
class ArtifactResult:
    template_id: str
    zip_path: Path
    checksum_path: Path
    report_path: Path
    preview_path: Optional[Path]
    sha256: str
    file_count: int
    compilation_results: tuple[CompilationResult, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_relative(value: str, context: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ArtifactError(f"unsafe {context}: {value!r}")
    return path


def _generated_path(relative: PurePosixPath) -> Optional[str]:
    if any(part in GENERATED_DIRECTORIES for part in relative.parts[:-1]):
        return "generated-directory"
    if relative.name in GENERATED_FILENAMES:
        return "generated-file"
    name = relative.name
    if any(name.endswith(suffix) for suffix in GENERATED_SUFFIXES):
        return "generated-file"
    return None


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    mode = 0o755 if source.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) else 0o644
    destination.chmod(mode)


def _asset_index(template: Mapping[str, Any]) -> dict[PurePosixPath, Mapping[str, Any]]:
    return {
        _safe_relative(asset["local_path"], f"asset path for {asset['id']}"): asset
        for asset in template.get("assets", [])
    }


def _download_fetched_asset(asset: Mapping[str, Any], destination: Path) -> str:
    request = urllib.request.Request(
        asset["source_url"], headers={"User-Agent": "apograph-artifact-builder/1"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
    except Exception as exc:
        raise ArtifactError(f"could not fetch asset {asset['id']}: {exc}") from exc
    actual = hashlib.sha256(data).hexdigest()
    if actual != asset["sha256"]:
        raise ArtifactError(
            f"checksum mismatch for fetched asset {asset['id']}: "
            f"expected {asset['sha256']}, got {actual}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return actual


def _copy_template_source(
    template: Mapping[str, Any],
    source_dir: Path,
    stage_dir: Path,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    assets = _asset_index(template)
    excluded_entrypoints = {
        _safe_relative(entrypoint["path"], "entry point")
        for entrypoint in template.get("entrypoints", [])
        if not entrypoint.get("include_in_artifact")
    }
    skipped: list[dict[str, str]] = []
    asset_report: list[dict[str, Any]] = []

    for source in sorted(source_dir.rglob("*")):
        if not source.is_file():
            continue
        if source.is_symlink():
            raise ArtifactError(f"template source symlinks are not permitted: {source}")
        relative = PurePosixPath(source.relative_to(source_dir).as_posix())
        reason = _generated_path(relative)
        if reason:
            skipped.append({"path": relative.as_posix(), "reason": reason})
            continue
        if relative in excluded_entrypoints:
            skipped.append({"path": relative.as_posix(), "reason": "catalog-excluded-entrypoint"})
            continue

        asset = assets.get(relative)
        if asset is not None:
            mode = asset["mode"]
            if mode == "bundled":
                _copy_file(source, stage_dir / Path(*relative.parts))
                asset_report.append(
                    {
                        "id": asset["id"],
                        "mode": mode,
                        "path": relative.as_posix(),
                        "included": True,
                        "sha256": sha256_file(source),
                    }
                )
            else:
                skipped.append({"path": relative.as_posix(), "reason": f"asset-mode-{mode}"})
            continue

        if "theme" in relative.parts and "assets" in relative.parts:
            # Only declared theme assets can become release inputs. Instructional
            # markers and empty-directory sentinels remain harmless source files.
            if relative.name == ".gitkeep" or relative.name.endswith(".placeholder"):
                _copy_file(source, stage_dir / Path(*relative.parts))
            else:
                skipped.append({"path": relative.as_posix(), "reason": "undeclared-theme-asset"})
            continue

        _copy_file(source, stage_dir / Path(*relative.parts))

    for relative, asset in sorted(assets.items(), key=lambda item: item[0].as_posix()):
        if asset["mode"] == "bundled":
            if not (stage_dir / Path(*relative.parts)).is_file():
                raise ArtifactError(f"required bundled asset is missing: {relative}")
            continue
        if asset["mode"] == "user-provided":
            asset_report.append(
                {
                    "id": asset["id"],
                    "mode": "user-provided",
                    "path": relative.as_posix(),
                    "included": False,
                    "sha256": None,
                    "fallback": asset.get("fallback"),
                }
            )
        elif asset["mode"] == "placeholder":
            asset_report.append(
                {
                    "id": asset["id"],
                    "mode": "placeholder",
                    "path": relative.as_posix(),
                    "included": False,
                    "sha256": None,
                    "fallback": asset.get("fallback"),
                }
            )
    return skipped, asset_report


def _apply_nonbundled_assets(
    template: Mapping[str, Any],
    stage_dir: Path,
    asset_report: list[dict[str, Any]],
    *,
    fetch_assets: bool,
) -> None:
    reported = {item["id"] for item in asset_report}
    for asset in template.get("assets", []):
        if asset["id"] in reported or asset["mode"] == "bundled":
            continue
        relative = _safe_relative(asset["local_path"], f"asset path for {asset['id']}")
        destination = stage_dir / Path(*relative.parts)
        mode = asset["mode"]
        if mode == "fetched" and fetch_assets:
            checksum = _download_fetched_asset(asset, destination)
            asset_report.append(
                {
                    "id": asset["id"],
                    "mode": mode,
                    "path": relative.as_posix(),
                    "included": True,
                    "sha256": checksum,
                }
            )
        elif mode == "fetched":
            if asset.get("required") or not asset.get("fallback"):
                raise ArtifactError(
                    f"fetched asset {asset['id']} is required; rerun with --fetch-assets"
                )
            asset_report.append(
                {
                    "id": asset["id"],
                    "mode": mode,
                    "path": relative.as_posix(),
                    "included": False,
                    "sha256": None,
                    "fallback": asset.get("fallback"),
                }
            )
        elif mode == "generated":
            raise ArtifactError(f"generated asset is not yet backed by a generator: {asset['id']}")
        elif mode not in {"user-provided", "placeholder"}:
            raise ArtifactError(f"unsupported asset mode for {asset['id']}: {mode}")


def _vendor_shared_dependencies(
    template: Mapping[str, Any],
    repo_root: Path,
    stage_dir: Path,
) -> list[dict[str, str]]:
    report: list[dict[str, str]] = []
    destinations: dict[str, str] = {}
    for dependency in template.get("shared_deps", []):
        relative = _safe_relative(dependency, "shared dependency")
        source = repo_root / Path(*relative.parts)
        if not source.is_file():
            raise ArtifactError(f"shared dependency does not exist: {relative}")
        if source.is_symlink():
            raise ArtifactError(f"shared dependency symlinks are not permitted: {relative}")
        destination = stage_dir / relative.name
        checksum = sha256_file(source)
        previous = destinations.get(relative.name)
        if previous is not None and previous != checksum:
            raise ArtifactError(f"shared dependencies collide at artifact root: {relative.name}")
        if destination.exists() and sha256_file(destination) != checksum:
            raise ArtifactError(f"shared dependency conflicts with template file: {relative.name}")
        _copy_file(source, destination)
        destinations[relative.name] = checksum
        report.append(
            {
                "source": relative.as_posix(),
                "artifact_path": relative.name,
                "sha256": checksum,
            }
        )
    return report


def _editor_files(stage_dir: Path, template: Mapping[str, Any]) -> None:
    vscode = stage_dir / ".vscode"
    vscode.mkdir(exist_ok=True)
    compiler = template.get("compiler")
    if template.get("format") == "latex":
        flag = {"pdflatex": "-pdf", "lualatex": "-lualatex", "xelatex": "-xelatex"}[compiler]
        settings = {
            "latex-workshop.latex.outDir": "%DIR%/out",
            "latex-workshop.latex.tools": [
                {
                    "name": "latexmk",
                    "command": "latexmk",
                    "args": [
                        flag,
                        "-interaction=nonstopmode",
                        "-file-line-error",
                        "-outdir=%OUTDIR%",
                        "%DOC%",
                    ],
                }
            ],
            "latex-workshop.latex.recipes": [{"name": f"latexmk ({compiler})", "tools": ["latexmk"]}],
        }
        recommendations = ["james-yu.latex-workshop", "valentjn.vscode-ltex"]
    else:
        settings = {}
        recommendations = ["myriad-dreamin.tinymist", "valentjn.vscode-ltex"]
    (vscode / "settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    (vscode / "extensions.json").write_text(
        json.dumps({"recommendations": recommendations}, indent=2) + "\n",
        encoding="utf-8",
    )


def _artifact_readme(
    template: Mapping[str, Any],
    *,
    release_version: str,
    source_commit: Optional[str],
) -> str:
    lines = [
        f"# {template['name']}",
        "",
        template["description"],
        "",
        f"Apograph template ID: `{template['id']}`. Maturity: **{template['status']}**.",
    ]
    if template["status"] == "draft":
        lines.extend(["", "> This is a draft and is not a public release-ready template."])
    entrypoints = [
        entrypoint["path"]
        for entrypoint in template.get("entrypoints", [])
        if entrypoint.get("include_in_artifact")
    ]
    lines.extend(["", "## Start", ""])
    if template.get("format") == "latex":
        lines.append(f"Compile `{entrypoints[0]}` with `{template['compiler']}`/`latexmk`.")
    else:
        lines.append(f"Compile `{entrypoints[0]}` with Typst.")

    user_assets = [asset for asset in template.get("assets", []) if asset["mode"] == "user-provided"]
    if user_assets:
        lines.extend(
            [
                "",
                "## Optional institution assets",
                "",
                "Institution marks are not redistributed with this template. Obtain an authorized",
                "copy under the institution's current brand rules and place it at the exact path",
                "below. The template compiles without it by using the documented fallback.",
                "",
            ]
        )
        for asset in user_assets:
            lines.append(
                f"- `{asset['local_path']}` — {asset['description']}; fallback: "
                f"`{asset.get('fallback') or 'none'}`."
            )
        lines.extend(
            [
                "",
                "Apograph intentionally provides no automatic logo download URL: public",
                "accessibility is not evidence of redistribution or trademark permission.",
            ]
        )

    lines.extend(
        [
            "",
            "## Provenance",
            "",
            "This README and `template.json` were generated from Apograph's catalog.",
            "See `template.json` for template, asset, license, and upstream metadata.",
            f"Collection release: `v{release_version}`.",
            f"Source commit: `{source_commit or 'developer build (uncommitted)'}`.",
            "Report problems at https://github.com/eliainnocenti/apograph/issues.",
            "",
        ]
    )
    return "\n".join(lines)


def _file_manifest(stage_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(stage_dir).as_posix(),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in sorted(stage_dir.rglob("*"))
        if path.is_file() and path.name != "template.json"
    ]


def _write_metadata(
    stage_dir: Path,
    template: Mapping[str, Any],
    *,
    catalog_schema_version: str,
    release_version: str,
    source_commit: Optional[str],
    source_date_epoch: int,
    shared: list[dict[str, str]],
    assets: list[dict[str, Any]],
) -> None:
    metadata = dict(template)
    metadata.pop("source_dir", None)
    metadata["artifact"] = {
        "format_version": "1.0.0",
        "catalog_schema_version": catalog_schema_version,
        "release_version": release_version,
        "source_commit": source_commit,
        "source_date_epoch": source_date_epoch,
        "built_at": dt.datetime.fromtimestamp(source_date_epoch, tz=dt.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "shared_dependencies": shared,
        "assets": assets,
        "files": _file_manifest(stage_dir),
        "checksum_file": f"{template['id']}.zip.sha256",
    }
    (stage_dir / "template.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _validate_stage(template: Mapping[str, Any], stage_dir: Path) -> None:
    for entrypoint in template.get("entrypoints", []):
        path = _safe_relative(entrypoint["path"], "entry point")
        exists = (stage_dir / Path(*path.parts)).is_file()
        if entrypoint.get("include_in_artifact") and not exists:
            raise ArtifactError(f"artifact entry point is missing: {path}")
        if not entrypoint.get("include_in_artifact") and exists:
            raise ArtifactError(f"excluded entry point leaked into artifact: {path}")
        if entrypoint.get("role") == "starter" and entrypoint.get("include_in_artifact"):
            if len(path.parts) != 1:
                raise ArtifactError(f"starter entry point must be at artifact root: {path}")


def _zip_datetime(source_date_epoch: int) -> tuple[int, int, int, int, int, int]:
    timestamp = max(source_date_epoch, FIXED_EPOCH)
    value = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
    # ZIP stores seconds in two-second increments.
    return (value.year, value.month, value.day, value.hour, value.minute, value.second // 2 * 2)


def _write_deterministic_zip(stage_dir: Path, destination: Path, source_date_epoch: int) -> None:
    timestamp = _zip_datetime(source_date_epoch)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in stage_dir.rglob("*") if item.is_file()):
            relative = path.relative_to(stage_dir).as_posix()
            info = zipfile.ZipInfo(relative, date_time=timestamp)
            info.create_system = 3
            mode = 0o755 if path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info.flag_bits |= 0x800
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _output_paths(output_dir: Path, template: Mapping[str, Any]) -> dict[str, Path]:
    template_id = template["id"]
    preview_declared = any(entrypoint.get("preview") for entrypoint in template.get("entrypoints", []))
    return {
        "zip": output_dir / f"{template_id}.zip",
        "checksum": output_dir / f"{template_id}.zip.sha256",
        "report": output_dir / f"{template_id}.build.json",
        "preview": output_dir / f"{template_id}.preview.pdf" if preview_declared else None,
    }


def _require_clean_release_checkout(repo_root: Path, source_commit: str) -> None:
    """Ensure release bytes are attributable to the recorded checked-out commit."""
    command = ["git", "status", "--porcelain", "--untracked-files=all"]
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise ArtifactError(f"could not verify release checkout with git: {exc}") from exc
    if completed.returncode != 0:
        raise ArtifactError(
            f"git could not verify release checkout: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    if completed.stdout.strip():
        raise ArtifactError(
            "release mode requires a clean checkout; tracked or untracked changes were found"
        )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if revision.returncode != 0:
        raise ArtifactError(f"could not resolve release commit: {revision.stderr.strip()}")
    if revision.stdout.strip() != source_commit:
        raise ArtifactError(
            f"--source-commit {source_commit} does not match checked-out HEAD {revision.stdout.strip()}"
        )


def build_artifact(
    template: Mapping[str, Any],
    output_dir: Path,
    *,
    repo_root: Path = REPO_ROOT,
    catalog_schema_version: str = "1.0.0",
    release_version: str = "0.0.0-dev",
    source_commit: Optional[str] = None,
    source_date_epoch: Optional[int] = None,
    include_vscode: bool = True,
    fetch_assets: bool = False,
    verify: bool = True,
    release_mode: bool = False,
    force: bool = False,
    keep_failed: bool = False,
) -> ArtifactResult:
    """Build, optionally compile, and report one canonical artifact."""
    if release_mode and template.get("status") not in {"beta", "stable"}:
        raise ArtifactError(f"release mode rejects {template.get('status')} template {template['id']}")
    if release_mode and not source_commit:
        raise ArtifactError("release mode requires --source-commit (or GITHUB_SHA)")
    if release_mode:
        _require_clean_release_checkout(repo_root, source_commit)
    source_dir = repo_root / template["source_dir"]
    if not source_dir.is_dir():
        raise ArtifactError(f"template source directory does not exist: {source_dir}")
    if source_dir.is_symlink():
        raise ArtifactError(f"template source directory may not be a symlink: {source_dir}")

    output_dir = output_dir.resolve()
    resolved_source = source_dir.resolve()
    if output_dir == resolved_source or resolved_source in output_dir.parents:
        raise ArtifactError("output directory may not be inside the template source directory")
    outputs = _output_paths(output_dir, template)
    existing = [path for path in outputs.values() if path is not None and path.exists()]
    if existing and not force:
        names = ", ".join(path.name for path in existing)
        raise ArtifactError(f"refusing to overwrite existing output: {names}; pass --force")
    output_dir.mkdir(parents=True, exist_ok=True)

    epoch = source_date_epoch
    if epoch is None:
        raw_epoch = os.environ.get("SOURCE_DATE_EPOCH")
        epoch = int(raw_epoch) if raw_epoch is not None else FIXED_EPOCH
    if epoch < 0:
        raise ArtifactError("SOURCE_DATE_EPOCH may not be negative")

    # Keep the complete staging transaction on the destination filesystem.
    # CI mounts GITHUB_WORKSPACE separately from /tmp, so publishing a /tmp
    # delivery with os.replace would fail with EXDEV instead of remaining
    # atomic.
    temp_root = Path(
        tempfile.mkdtemp(
            prefix=f".apograph-{template['id']}-",
            dir=output_dir,
        )
    )
    stage_dir = temp_root / "artifact"
    compile_dir = stage_dir / ".apograph-build"
    delivery_dir = temp_root / "delivery"
    stage_dir.mkdir()
    delivery_dir.mkdir()
    temporary_outputs = _output_paths(delivery_dir, template)
    success = False
    try:
        skipped, assets = _copy_template_source(template, source_dir, stage_dir)
        _apply_nonbundled_assets(template, stage_dir, assets, fetch_assets=fetch_assets)
        shared = _vendor_shared_dependencies(template, repo_root, stage_dir)
        if include_vscode:
            _editor_files(stage_dir, template)
        readme_path = stage_dir / "README.md"
        generated_readme_name = "README.md" if not readme_path.exists() else "APOGRAPH.md"
        (stage_dir / generated_readme_name).write_text(
            _artifact_readme(
                template,
                release_version=release_version,
                source_commit=source_commit,
            ),
            encoding="utf-8",
        )
        _write_metadata(
            stage_dir,
            template,
            catalog_schema_version=catalog_schema_version,
            release_version=release_version,
            source_commit=source_commit,
            source_date_epoch=epoch,
            shared=shared,
            assets=assets,
        )
        _validate_stage(template, stage_dir)

        compilation_results: list[CompilationResult] = []
        if verify:
            try:
                compile_environment = dict(os.environ)
                compile_environment["SOURCE_DATE_EPOCH"] = str(epoch)
                compile_environment["FORCE_SOURCE_DATE"] = "1"
                compile_environment["TZ"] = "UTC"
                compilation_results = compile_entrypoints(
                    template,
                    stage_dir,
                    compile_dir,
                    environment=compile_environment,
                )
            except CompilationError as exc:
                tail = "\n".join(exc.output.splitlines()[-40:])
                details = f"\n{tail}" if tail else ""
                raise ArtifactError(f"artifact compilation failed: {exc}{details}") from exc

        preview_path = None
        if verify and temporary_outputs["preview"] is not None:
            preview_path = copy_preview(template, compilation_results, temporary_outputs["preview"])
        if compile_dir.exists():
            shutil.rmtree(compile_dir)

        _write_deterministic_zip(stage_dir, temporary_outputs["zip"], epoch)
        checksum = sha256_file(temporary_outputs["zip"])
        temporary_outputs["checksum"].write_text(
            f"{checksum}  {outputs['zip'].name}\n", encoding="utf-8"
        )
        report = {
            "format_version": "1.0.0",
            "template_id": template["id"],
            "status": template["status"],
            "mode": "release" if release_mode else "developer",
            "release_version": release_version,
            "source_commit": source_commit,
            "source_date_epoch": epoch,
            "artifact": {
                "path": outputs["zip"].name,
                "sha256": checksum,
                "size": temporary_outputs["zip"].stat().st_size,
                "file_count": sum(1 for path in stage_dir.rglob("*") if path.is_file()),
            },
            "preview": {
                "path": outputs["preview"].name,
                "sha256": sha256_file(preview_path),
                "size": preview_path.stat().st_size,
            }
            if preview_path
            else None,
            "shared_dependencies": shared,
            "assets": assets,
            "source_selection": {
                "policy_version": "1.0.0",
                "excluded_entrypoints": sorted(
                    entrypoint["path"]
                    for entrypoint in template.get("entrypoints", [])
                    if not entrypoint.get("include_in_artifact")
                ),
            },
            "compilation": [
                {
                    "entrypoint": result.entrypoint,
                    "compiler": result.compiler,
                    "command": [
                        "-outdir=<isolated-output>"
                        if item.startswith("-outdir=")
                        else "<isolated-output>"
                        if item == str(result.pdf_path)
                        else item
                        for item in result.command
                    ],
                    "pdf": f"{Path(result.entrypoint).stem}.pdf",
                }
                for result in compilation_results
            ],
        }
        temporary_outputs["report"].write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if not force:
            raced = [path for path in outputs.values() if path is not None and path.exists()]
            if raced:
                names = ", ".join(path.name for path in raced)
                raise ArtifactError(f"output appeared during build; refusing to overwrite: {names}")
        for key, temporary_path in temporary_outputs.items():
            if temporary_path is not None and temporary_path.exists():
                os.replace(temporary_path, outputs[key])
        preview_path = outputs["preview"] if preview_path else None
        success = True
        return ArtifactResult(
            template_id=template["id"],
            zip_path=outputs["zip"],
            checksum_path=outputs["checksum"],
            report_path=outputs["report"],
            preview_path=preview_path,
            sha256=checksum,
            file_count=report["artifact"]["file_count"],
            compilation_results=tuple(compilation_results),
        )
    except Exception as exc:
        if keep_failed:
            if isinstance(exc, ArtifactError):
                exc.debug_dir = temp_root
                raise
            raise ArtifactError(str(exc), debug_dir=temp_root) from exc
        raise
    finally:
        if success or not keep_failed:
            shutil.rmtree(temp_root, ignore_errors=True)
