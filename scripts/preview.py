#!/usr/bin/env python3
"""
preview.py — Compile all apograph templates and generate preview PDFs.

Reads CATALOG.json, compiles each template using the appropriate compiler
(latexmk for LaTeX, typst for Typst), and copies the resulting PDFs
as preview files.

Usage:
    python scripts/preview.py              # compile all templates
    python scripts/preview.py <template-id> # compile a specific template
    python scripts/preview.py --list       # list all templates

Requires:
    - Python 3.8+
    - latexmk (for LaTeX templates) — included with MacTeX / TeX Live
    - typst (for Typst templates) — install from https://typst.app
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from catalog import PUBLIC_STATUSES, require_valid_catalog, select_entrypoint


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "CATALOG.json"

# Map compiler names to latexmk flags
LATEXMK_FLAGS = {
    "pdflatex": ["-pdf"],
    "lualatex": ["-lualatex"],
    "xelatex": ["-xelatex"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_catalog() -> dict:
    """Load and return the CATALOG.json contents."""
    if not CATALOG_PATH.exists():
        print(f"Error: CATALOG.json not found at {CATALOG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    require_valid_catalog(catalog)
    return catalog


def compile_latex(template_entry: dict) -> bool:
    """
    Compile a LaTeX template using latexmk.

    Returns True on success, False on failure.
    """
    template_id = template_entry["id"]
    source_dir = REPO_ROOT / template_entry["source_dir"]
    main_file = select_entrypoint(template_entry, preview=True).get("path", "main.tex")
    compiler = template_entry.get("compiler", "pdflatex")

    main_path = source_dir / main_file
    if not main_path.exists():
        print(f"  ⚠ Main file not found: {main_path}")
        return False

    # Build the latexmk command
    flags = LATEXMK_FLAGS.get(compiler, ["-pdf"])
    cmd = [
        "latexmk",
        *flags,
        "-synctex=1",
        "-interaction=nonstopmode",
        "-file-line-error",
        f"-outdir={source_dir / 'out'}",
        str(main_path),
    ]

    # Set TEXINPUTS to include shared/latex/ directory
    env = os.environ.copy()
    shared_latex = REPO_ROOT / "shared" / "latex"
    texinputs = f"{source_dir}:{shared_latex}//:"
    if "TEXINPUTS" in env:
        texinputs += env["TEXINPUTS"]
    env["TEXINPUTS"] = texinputs

    print(f"  Compiling with {compiler}...")
    try:
        # Ensure the output directory exists
        (source_dir / "out").mkdir(exist_ok=True)
        result = subprocess.run(
            cmd,
            cwd=source_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute timeout per template
        )

        if result.returncode != 0:
            print(f"  ✗ Compilation failed for {template_id}")
            # Print last 20 lines of output for debugging
            log_lines = result.stdout.strip().split("\n")
            for line in log_lines[-20:]:
                print(f"    {line}")
            return False

        # Find the output PDF
        pdf_name = Path(main_file).stem + ".pdf"
        pdf_path = source_dir / "out" / pdf_name

        if pdf_path.exists():
            # Copy as preview.pdf one level up (next to the language dir)
            preview_dir = source_dir.parent
            preview_path = preview_dir / "preview.pdf"
            import shutil
            shutil.copy2(pdf_path, preview_path)
            print(f"  ✓ Preview: {preview_path.relative_to(REPO_ROOT)}")
            return True
        else:
            print(f"  ⚠ PDF not found after compilation: {pdf_path}")
            return False

    except FileNotFoundError:
        print(f"  ✗ '{compiler}' not found. Install TeX Live / MacTeX.")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Compilation timed out (>120s)")
        return False


def compile_typst(template_entry: dict) -> bool:
    """
    Compile a Typst template.

    Returns True on success, False on failure.
    """
    template_id = template_entry["id"]
    source_dir = REPO_ROOT / template_entry["source_dir"]
    main_file = select_entrypoint(template_entry, preview=True).get("path", "main.typ")

    main_path = source_dir / main_file
    if not main_path.exists():
        print(f"  ⚠ Main file not found: {main_path}")
        return False

    pdf_name = Path(main_file).stem + ".pdf"
    pdf_path = source_dir / pdf_name

    cmd = ["typst", "compile", str(main_path), str(pdf_path)]

    print(f"  Compiling with typst...")
    try:
        result = subprocess.run(
            cmd,
            cwd=source_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"  ✗ Compilation failed for {template_id}")
            print(f"    {result.stderr.strip()}")
            return False

        if pdf_path.exists():
            preview_dir = source_dir.parent
            preview_path = preview_dir / "preview.pdf"
            import shutil
            shutil.copy2(pdf_path, preview_path)
            print(f"  ✓ Preview: {preview_path.relative_to(REPO_ROOT)}")
            return True
        else:
            print(f"  ⚠ PDF not found after compilation: {pdf_path}")
            return False

    except FileNotFoundError:
        print("  ✗ 'typst' not found. Install from https://typst.app")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Compilation timed out (>60s)")
        return False


def compile_template(template_entry: dict) -> bool:
    """Compile a template using the appropriate compiler."""
    language = template_entry.get("format", template_entry.get("language", "latex"))

    if language == "latex":
        return compile_latex(template_entry)
    elif language == "typst":
        return compile_typst(template_entry)
    else:
        print(f"  ⚠ Unknown language: {language}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compile apograph templates and generate preview PDFs.",
        epilog="Examples:\n"
               "  python scripts/preview.py\n"
               "  python scripts/preview.py thesis-polito-msc-latex\n"
               "  python scripts/preview.py --list\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "template_id",
        nargs="?",
        help="Template ID to compile (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available templates",
    )

    args = parser.parse_args()
    catalog = load_catalog()
    templates = catalog.get("templates", [])

    if args.list:
        print(f"Available templates ({len(templates)}):\n")
        for t in templates:
            print(f"  {t['id']:45s}  {t['status']:10s}  {t['name']}")
        return

    if args.template_id:
        # Compile a specific template
        entry = None
        for t in templates:
            if t["id"] == args.template_id:
                entry = t
                break

        if entry is None:
            available = [t["id"] for t in templates]
            print(f"Error: template '{args.template_id}' not found.", file=sys.stderr)
            print(f"Available: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)

        print(f"Compiling: {entry['id']}")
        success = compile_template(entry)
        sys.exit(0 if success else 1)

    else:
        # Compile all templates
        templates = [t for t in templates if t.get("status") in PUBLIC_STATUSES]
        if not templates:
            print("No beta/stable templates are currently eligible for default compilation.")
            print("Compile a draft explicitly by template ID when developing it.")
            return

        print(f"Compiling all {len(templates)} public templates...\n")
        results = {"pass": [], "fail": [], "skip": []}

        for entry in templates:
            print(f"[{entry['id']}]")
            success = compile_template(entry)
            if success:
                results["pass"].append(entry["id"])
            else:
                results["fail"].append(entry["id"])
            print()

        # Summary
        total = len(templates)
        passed = len(results["pass"])
        failed = len(results["fail"])

        print("=" * 60)
        print(f"Results: {passed}/{total} passed, {failed}/{total} failed")

        if results["fail"]:
            print(f"\nFailed templates:")
            for tid in results["fail"]:
                print(f"  ✗ {tid}")

        sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
