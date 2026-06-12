#!/usr/bin/env python3
"""
pack.py — Bundle an apograph template into a self-contained ZIP.

Reads CATALOG.json to find the template entry, copies the template source
directory along with all shared dependencies, rewrites \\input{} and
\\usepackage{} paths to point at the bundled copies, fetches institutional
assets (logos) at runtime, and produces a ZIP ready for Overleaf or local use.

Usage:
    python scripts/pack.py <template-id>              # pack one template
    python scripts/pack.py --all                       # pack all templates
    python scripts/pack.py <template-id> --vscode      # include .vscode/ config
    python scripts/pack.py <template-id> --no-assets    # skip asset download
    python scripts/pack.py <template-id> --out ./dist   # custom output directory

Requires: Python 3.8+ (no external dependencies)
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "CATALOG.json"
DEFAULT_BUILD_DIR = REPO_ROOT / "build"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_catalog() -> dict:
    """Load and return the CATALOG.json contents."""
    if not CATALOG_PATH.exists():
        print(f"Error: CATALOG.json not found at {CATALOG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_template(catalog: dict, template_id: str) -> dict | None:
    """Find a template entry by ID in the catalog."""
    for entry in catalog.get("templates", []):
        if entry["id"] == template_id:
            return entry
    return None


def rewrite_shared_paths(file_path: Path, shared_dir_name: str = "shared") -> None:
    """
    Rewrite LaTeX \\input{} and \\usepackage{} paths that reference the
    repo's shared/ directory to point at the bundled local copy instead.

    Handles patterns like:
        \\usepackage{../../../../shared/latex/apograph-math}
        \\input{../../../../shared/latex/apograph-math.sty}
    And rewrites them to:
        \\usepackage{shared/apograph-math}
        \\input{shared/apograph-math.sty}
    """
    if not file_path.suffix in (".tex", ".sty", ".cls"):
        return

    content = file_path.read_text(encoding="utf-8")
    original = content

    # Pattern: any relative path to shared/latex/... in \usepackage or \input
    # Matches: \usepackage{../../shared/latex/apograph-math}
    #          \input{../../../shared/latex/apograph-math.sty}
    pattern = r"(\\(?:usepackage|input|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{)" \
              r"(?:[./]*shared/latex/)" \
              r"([^}]+)\}"

    def replacer(match):
        prefix = match.group(1)
        filename = match.group(2)
        return f"{prefix}{shared_dir_name}/{filename}}}"

    content = re.sub(pattern, replacer, content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")


def create_vscode_config(dest_dir: Path, template_entry: dict) -> None:
    """Create a .vscode/ directory with settings for the packed template."""
    vscode_dir = dest_dir / ".vscode"
    vscode_dir.mkdir(exist_ok=True)

    compiler = template_entry.get("compiler", "pdflatex")

    # Map compiler to latexmk flag
    compiler_flag = {
        "pdflatex": "-pdf",
        "lualatex": "-lualatex",
        "xelatex": "-xelatex",
    }.get(compiler, "-pdf")

    settings = {
        "latex-workshop.latex.outDir": "%DIR%/out",
        "latex-workshop.latex.clean.subfolder.enabled": True,
        "latex-workshop.latex.tools": [
            {
                "name": "latexmk",
                "command": "latexmk",
                "args": [
                    "-synctex=1",
                    "-interaction=nonstopmode",
                    "-file-line-error",
                    compiler_flag,
                    "-outdir=%OUTDIR%",
                    "%DOC%",
                ],
            }
        ],
        "latex-workshop.latex.recipes": [
            {"name": f"latexmk ({compiler})", "tools": ["latexmk"]}
        ],
        "latex-workshop.view.pdf.viewer": "tab",
        "latex-workshop.latex.autoBuild.run": "onSave",
        "latex-workshop.latex.autoClean.run": "onSucceeded",
    }

    extensions = {
        "recommendations": [
            "james-yu.latex-workshop",
            "valentjn.vscode-ltex",
            "streetsidesoftware.code-spell-checker",
        ]
    }

    # Add Tinymist for Typst templates
    if template_entry.get("language") == "typst":
        extensions["recommendations"].insert(1, "myriad-dreamin.tinymist")

    (vscode_dir / "settings.json").write_text(
        json.dumps(settings, indent=2) + "\n", encoding="utf-8"
    )
    (vscode_dir / "extensions.json").write_text(
        json.dumps(extensions, indent=2) + "\n", encoding="utf-8"
    )


def fetch_assets_for_build(
    template_entry: dict,
    build_dir: Path,
) -> dict:
    """
    Fetch institutional assets (logos, etc.) into the build directory.

    Uses the assets module to download from official URLs.
    Falls back gracefully — the template will compile with placeholder boxes.
    """
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.assets import download_asset, is_asset_present

    assets = template_entry.get("assets", [])
    if not assets:
        return {"fetched": 0, "failed": 0}

    results = {"fetched": 0, "failed": 0}

    for asset in assets:
        url = asset.get("official_url")
        local_path = build_dir / asset.get("local_path", "")
        description = asset.get("description", asset.get("id", "unknown"))

        if not url:
            print(f"  ⚠ No URL configured for {description} (placeholder will be used)")
            results["failed"] += 1
            continue

        success = download_asset(url, local_path, description)
        if success:
            results["fetched"] += 1
        else:
            results["failed"] += 1

    return results


def pack_template(
    template_entry: dict,
    output_dir: Path,
    include_vscode: bool = False,
    fetch_assets: bool = True,
) -> Path:
    """
    Bundle a single template into a self-contained ZIP.

    Returns the path to the created ZIP file.
    """
    template_id = template_entry["id"]
    source_dir = REPO_ROOT / template_entry["source_dir"]

    if not source_dir.exists():
        print(f"Error: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Packing: {template_id}")
    print(f"  Source: {source_dir}")

    # Create a temporary build directory
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp) / template_id

        # 1. Copy the template source (ignore out/ dir and LaTeX aux/pdf files)
        shutil.copytree(
            source_dir,
            build_dir,
            ignore=shutil.ignore_patterns("out", "*.pdf", "*.synctex*", "*.aux", "*.log", "*.fls", "*.fdb_latexmk")
        )
        print(f"  Copied template source ({sum(1 for _ in build_dir.rglob('*'))} files)")

        # 2. Copy shared dependencies into build_dir/shared/
        shared_deps = template_entry.get("shared_deps", [])
        if shared_deps:
            shared_dest = build_dir / "shared"
            shared_dest.mkdir(exist_ok=True)

            for dep_path in shared_deps:
                dep_full = REPO_ROOT / dep_path
                if dep_full.exists():
                    shutil.copy2(dep_full, shared_dest / dep_full.name)
                else:
                    print(f"  Warning: shared dependency not found: {dep_path}",
                          file=sys.stderr)

            print(f"  Bundled {len(shared_deps)} shared dependencies")

        # 3. Rewrite paths in .tex, .sty, .cls files
        for tex_file in build_dir.rglob("*"):
            if tex_file.is_file():
                rewrite_shared_paths(tex_file)

        # 4. Create template.json from catalog entry
        template_meta = {
            k: v for k, v in template_entry.items()
            if k not in ("source_dir", "release_zip_url", "preview_pdf_url")
        }
        (build_dir / "template.json").write_text(
            json.dumps(template_meta, indent=2) + "\n", encoding="utf-8"
        )

        # 5. Optionally add .vscode/ config
        if include_vscode:
            create_vscode_config(build_dir, template_entry)
            print("  Added .vscode/ configuration")

        # 6. Fetch institutional assets (logos, etc.)
        if fetch_assets:
            asset_results = fetch_assets_for_build(template_entry, build_dir)
            if asset_results["fetched"] > 0:
                print(f"  Fetched {asset_results['fetched']} asset(s)")
            if asset_results["failed"] > 0:
                print(f"  ⚠ {asset_results['failed']} asset(s) unavailable (placeholders used)")

        # 7. Create ZIP
        output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = output_dir / f"{template_id}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(build_dir.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(build_dir)
                    zf.write(file_path, arcname)

        zip_size = zip_path.stat().st_size
        print(f"  Created: {zip_path} ({zip_size:,} bytes)")

    return zip_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bundle apograph templates into self-contained ZIPs.",
        epilog="Examples:\n"
               "  python scripts/pack.py thesis-polito-msc-latex\n"
               "  python scripts/pack.py --all\n"
               "  python scripts/pack.py thesis-polito-msc-latex --vscode\n"
               "  python scripts/pack.py thesis-polito-msc-latex --no-assets\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "template_id",
        nargs="?",
        help="Template ID to pack (e.g., thesis-polito-msc-latex)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Pack all templates in the catalog",
    )
    parser.add_argument(
        "--vscode",
        action="store_true",
        help="Include .vscode/ configuration in the ZIP",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help=f"Output directory for ZIPs (default: {DEFAULT_BUILD_DIR})",
    )
    parser.add_argument(
        "--no-assets",
        action="store_true",
        help="Skip downloading institutional assets (logos, etc.)",
    )

    args = parser.parse_args()

    if not args.template_id and not args.all:
        parser.error("Provide a template ID or use --all")

    catalog = load_catalog()

    if args.all:
        templates = catalog.get("templates", [])
        if not templates:
            print("No templates found in CATALOG.json", file=sys.stderr)
            sys.exit(1)

        print(f"Packing all {len(templates)} templates...\n")
        zips = []
        for entry in templates:
            zip_path = pack_template(entry, args.out, args.vscode, not args.no_assets)
            zips.append(zip_path)
            print()

        print(f"Done! {len(zips)} ZIPs created in {args.out}/")

    else:
        entry = find_template(catalog, args.template_id)
        if entry is None:
            available = [t["id"] for t in catalog.get("templates", [])]
            print(f"Error: template '{args.template_id}' not found.", file=sys.stderr)
            print(f"Available templates: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)

        pack_template(entry, args.out, args.vscode, not args.no_assets)
        print("\nDone!")


if __name__ == "__main__":
    main()
