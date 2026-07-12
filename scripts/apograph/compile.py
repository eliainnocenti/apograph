"""Shared source and artifact compilation primitives.

Artifact compilation deliberately removes repository-specific TeX search paths.
Anything needed by a downloaded project must already be present in its root.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


LATEXMK_FLAGS = {
    "pdflatex": "-pdf",
    "lualatex": "-lualatex",
    "xelatex": "-xelatex",
}


@dataclass(frozen=True)
class CompilationResult:
    entrypoint: str
    compiler: str
    command: list[str]
    pdf_path: Path
    duration_seconds: float

    def report(self) -> dict[str, Any]:
        data = asdict(self)
        data["pdf_path"] = self.pdf_path.as_posix()
        data["duration_seconds"] = round(self.duration_seconds, 3)
        return data


class CompilationError(RuntimeError):
    """Raised when an entry point cannot be compiled."""

    def __init__(self, message: str, *, command: Optional[list[str]] = None, output: str = ""):
        super().__init__(message)
        self.command = command or []
        self.output = output


def publishable_entrypoints(template: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return declared entry points that belong to the downloadable artifact."""
    return [
        entrypoint
        for entrypoint in template.get("entrypoints", [])
        if entrypoint.get("include_in_artifact") and entrypoint.get("role") != "test"
    ]


def _clean_environment(
    environment: Optional[Mapping[str, str]],
    source_shared_dir: Optional[Path],
) -> dict[str, str]:
    env = dict(os.environ if environment is None else environment)
    # Artifact builds must not pass accidentally because the checkout is on a
    # global TeX search path. Source builds may opt into the shared directory.
    env.pop("TEXINPUTS", None)
    env.pop("BIBINPUTS", None)
    env.pop("BSTINPUTS", None)
    if source_shared_dir is not None:
        env["TEXINPUTS"] = f"{source_shared_dir.resolve()}//:"
    return env


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=dict(env),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CompilationError(
            f"compiler executable not found: {command[0]}", command=command
        ) from exc
    except subprocess.TimeoutExpired as exc:
        captured = "\n".join(part for part in (exc.stdout, exc.stderr) if isinstance(part, str))
        raise CompilationError(
            f"compilation timed out after {timeout}s", command=command, output=captured
        ) from exc
    duration = time.monotonic() - started
    if completed.returncode != 0:
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        raise CompilationError(
            f"compiler exited with status {completed.returncode}",
            command=command,
            output=output,
        )
    return completed, duration


def compile_entrypoints(
    template: Mapping[str, Any],
    project_dir: Path,
    output_dir: Path,
    *,
    entrypoints: Optional[Iterable[Mapping[str, Any]]] = None,
    source_shared_dir: Optional[Path] = None,
    synctex: bool = False,
    timeout: int = 180,
    environment: Optional[Mapping[str, str]] = None,
) -> list[CompilationResult]:
    """Compile each selected entry point into an isolated output directory."""
    project_dir = project_dir.resolve()
    output_dir = output_dir.resolve()
    selected = list(entrypoints or publishable_entrypoints(template))
    if not selected:
        raise CompilationError(f"{template.get('id', 'template')} has no publishable entry points")

    env = _clean_environment(environment, source_shared_dir)
    results: list[CompilationResult] = []
    template_format = template.get("format")
    compiler = template.get("compiler")

    for entrypoint in selected:
        relative_path = Path(entrypoint["path"])
        source = project_dir / relative_path
        if not source.is_file():
            raise CompilationError(f"entry point does not exist: {relative_path.as_posix()}")

        entry_output = output_dir / relative_path.parent / relative_path.stem
        entry_output.mkdir(parents=True, exist_ok=True)

        if template_format == "latex":
            try:
                compiler_flag = LATEXMK_FLAGS[compiler]
            except KeyError as exc:
                raise CompilationError(f"unsupported LaTeX compiler: {compiler}") from exc
            try:
                latex_output = entry_output.relative_to(project_dir).as_posix()
            except ValueError:
                latex_output = str(entry_output)
            command = [
                "latexmk",
                compiler_flag,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                f"-outdir={latex_output}",
            ]
            if synctex:
                command.append("-synctex=1")
            command.append(relative_path.as_posix())
            _, duration = _run(command, cwd=project_dir, env=env, timeout=timeout)
            pdf_path = entry_output / f"{relative_path.stem}.pdf"
        elif template_format == "typst":
            pdf_path = entry_output / f"{relative_path.stem}.pdf"
            command = ["typst", "compile", relative_path.as_posix(), str(pdf_path)]
            _, duration = _run(command, cwd=project_dir, env=env, timeout=timeout)
        else:
            raise CompilationError(f"unsupported template format: {template_format}")

        if not pdf_path.is_file():
            raise CompilationError(
                f"compiler succeeded but did not produce {pdf_path}", command=command
            )
        results.append(
            CompilationResult(
                entrypoint=relative_path.as_posix(),
                compiler=str(compiler),
                command=command,
                pdf_path=pdf_path,
                duration_seconds=duration,
            )
        )

    return results


def copy_preview(
    template: Mapping[str, Any],
    results: Iterable[CompilationResult],
    destination: Path,
) -> Optional[Path]:
    """Copy the declared preview result without compiling the source tree again."""
    by_entrypoint = {result.entrypoint: result for result in results}
    preview_entry = next(
        (entry for entry in template.get("entrypoints", []) if entry.get("preview")),
        None,
    )
    if preview_entry is None:
        return None
    result = by_entrypoint.get(preview_entry["path"])
    if result is None:
        raise CompilationError(
            f"preview entry point was not compiled: {preview_entry['path']}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(result.pdf_path, destination)
    return destination
