#!/usr/bin/env python3
"""
assets.py — Dynamic asset resolution for apograph templates.

Downloads institutional assets (logos, etc.) from official university servers
at runtime. Never stores copyrighted assets in the repository — the user's
machine fetches them directly from the source.

Design:
    - CATALOG.json entries have an optional "assets" array
    - Each asset has an official_url, local_path, and fallback behavior
    - If download fails (offline, URL changed, 403), a LaTeX-compilable
      placeholder is generated so compilation never breaks
    - Subsequent runs skip already-downloaded assets (use --force to re-fetch)

Usage:
    python scripts/assets.py                          # fetch all assets
    python scripts/assets.py <template-id>            # fetch for one template
    python scripts/assets.py --status                 # check asset status
    python scripts/assets.py --clean                  # remove downloaded assets
    python scripts/assets.py --force                  # re-download everything

Requires: Python 3.8+ (no external dependencies — uses urllib)
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "CATALOG.json"

# Marker file placed alongside downloaded assets so we can distinguish
# "user placed this manually" from "we downloaded this"
MARKER_SUFFIX = ".apograph-fetched"

# Timeout for HTTP requests (seconds)
DOWNLOAD_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Placeholder generation
# ---------------------------------------------------------------------------

def generate_placeholder_pdf(output_path: Path, label: str = "Logo") -> None:
    """
    Generate a minimal LaTeX-compilable placeholder at the given path.

    Instead of creating an actual PDF (which would require a TeX installation),
    we create a simple text file that acts as a marker. The actual placeholder
    rendering is handled in LaTeX via \\IfFileExists in the branding .sty files.

    The branding packages use \\IfFileExists to check for the logo file.
    If it doesn't exist, they render a \\framebox placeholder directly in LaTeX.
    So we actually do NOT need to create a placeholder file at all — the absence
    of the file IS the trigger for the LaTeX fallback.

    This function creates a small marker file (.placeholder) that tells the user
    and scripts that the asset is missing.
    """
    placeholder_marker = output_path.with_suffix(output_path.suffix + ".placeholder")
    placeholder_marker.write_text(
        f"This is a placeholder for: {label}\n"
        f"Expected file: {output_path.name}\n"
        f"\n"
        f"The template will compile without this file (using a placeholder box).\n"
        f"To use the real logo, either:\n"
        f"  1. Run: make fetch-assets\n"
        f"  2. Download manually and save as: {output_path.name}\n",
        encoding="utf-8",
    )


def remove_placeholder(output_path: Path) -> None:
    """Remove the placeholder marker file if it exists."""
    placeholder_marker = output_path.with_suffix(output_path.suffix + ".placeholder")
    if placeholder_marker.exists():
        placeholder_marker.unlink()


# ---------------------------------------------------------------------------
# Asset download
# ---------------------------------------------------------------------------

def download_asset(url: str, output_path: Path, description: str = "") -> bool:
    """
    Download a single asset from a URL.

    Returns True on success, False on failure.
    Never raises — failures are handled gracefully.
    """
    if not url:
        print(f"    ⚠ No URL configured for: {description or output_path.name}")
        return False

    try:
        print(f"    📥 Downloading: {description or output_path.name}")
        print(f"       From: {url}")

        # Create a request with a browser-like User-Agent
        # (some university servers block urllib's default UA)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        )

        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
            # Check response status
            if response.status != 200:
                print(f"    ✗ Server returned status {response.status}")
                return False

            # Check content type — basic sanity check
            content_type = response.headers.get("Content-Type", "")
            data = response.read()

            if len(data) < 100:
                print(f"    ⚠ Downloaded file suspiciously small ({len(data)} bytes)")
                # Still save it — might be a valid tiny SVG or something
                # But warn the user

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            output_path.write_bytes(data)

            # Write a marker so we know this was auto-fetched (not manually placed)
            marker_path = output_path.with_name(output_path.name + MARKER_SUFFIX)
            marker_path.write_text(
                json.dumps({
                    "source_url": url,
                    "description": description,
                    "size_bytes": len(data),
                    "content_type": content_type,
                }, indent=2),
                encoding="utf-8",
            )

            # Remove placeholder marker if it existed
            remove_placeholder(output_path)

            size_kb = len(data) / 1024
            print(f"    ✓ Saved: {output_path.name} ({size_kb:.1f} KB)")
            return True

    except urllib.error.HTTPError as e:
        print(f"    ✗ HTTP error {e.code}: {e.reason}")
        if e.code == 403:
            print(f"      The university may have restricted access to this file.")
        elif e.code == 404:
            print(f"      The URL may have changed. Check the university's website.")
        return False

    except urllib.error.URLError as e:
        print(f"    ✗ Network error: {e.reason}")
        print(f"      Check your internet connection.")
        return False

    except TimeoutError:
        print(f"    ✗ Download timed out after {DOWNLOAD_TIMEOUT}s")
        return False

    except Exception as e:
        print(f"    ✗ Unexpected error: {e}")
        return False


def is_asset_present(output_path: Path) -> bool:
    """Check if an asset file exists (either downloaded or manually placed)."""
    return output_path.exists() and output_path.stat().st_size > 0


def is_asset_auto_fetched(output_path: Path) -> bool:
    """Check if an asset was auto-fetched (vs manually placed by user)."""
    marker = output_path.with_name(output_path.name + MARKER_SUFFIX)
    return marker.exists()


# ---------------------------------------------------------------------------
# Template-level operations
# ---------------------------------------------------------------------------

def fetch_template_assets(
    template_entry: dict,
    force: bool = False,
) -> dict:
    """
    Fetch all assets for a single template.

    Returns a dict with counts: {"fetched": N, "skipped": N, "failed": N}
    """
    template_id = template_entry["id"]
    source_dir = REPO_ROOT / template_entry["source_dir"]
    assets = template_entry.get("assets", [])

    if not assets:
        return {"fetched": 0, "skipped": 0, "failed": 0, "no_assets": True}

    results = {"fetched": 0, "skipped": 0, "failed": 0, "no_assets": False}

    for asset in assets:
        asset_id = asset.get("id", "unknown")
        url = asset.get("official_url")
        local_path = source_dir / asset.get("local_path", f"figures/{asset_id}")
        description = asset.get("description", asset_id)
        manual_url = asset.get("manual_download_url", "")

        # Skip if already present (unless --force)
        if is_asset_present(local_path) and not force:
            print(f"    ⊘ Already present: {local_path.name} (use --force to re-fetch)")
            results["skipped"] += 1
            continue

        # Attempt download
        if url:
            success = download_asset(url, local_path, description)
        else:
            success = False
            print(f"    ⚠ No official_url configured for: {description}")

        if success:
            results["fetched"] += 1
        else:
            results["failed"] += 1
            # Generate placeholder marker
            generate_placeholder(local_path, description, manual_url)

    return results


def generate_placeholder(
    output_path: Path,
    description: str,
    manual_url: str = "",
) -> None:
    """Generate placeholder info when download fails."""
    generate_placeholder_pdf(output_path, description)

    manual_note = ""
    if manual_url:
        manual_note = f"\n      Manual download: {manual_url}"

    print(f"    📋 Placeholder created. Template will compile with a placeholder box.")
    print(f"      To add the real asset, save it as: {output_path.relative_to(REPO_ROOT)}")
    if manual_note:
        print(manual_note)


def check_template_assets(template_entry: dict) -> list[dict]:
    """Check the status of all assets for a template."""
    source_dir = REPO_ROOT / template_entry["source_dir"]
    assets = template_entry.get("assets", [])
    statuses = []

    for asset in assets:
        local_path = source_dir / asset.get("local_path", "")
        present = is_asset_present(local_path)
        auto = is_asset_auto_fetched(local_path) if present else False

        statuses.append({
            "id": asset.get("id", "unknown"),
            "description": asset.get("description", ""),
            "local_path": str(local_path.relative_to(REPO_ROOT)),
            "present": present,
            "source": "auto-fetched" if auto else ("manual" if present else "missing"),
            "has_url": bool(asset.get("official_url")),
        })

    return statuses


def clean_template_assets(template_entry: dict) -> int:
    """
    Remove auto-fetched assets for a template.

    Only removes files that were downloaded by this script (identified by
    the .apograph-fetched marker). Manually placed files are preserved.

    Returns the number of files removed.
    """
    source_dir = REPO_ROOT / template_entry["source_dir"]
    assets = template_entry.get("assets", [])
    removed = 0

    for asset in assets:
        local_path = source_dir / asset.get("local_path", "")

        if is_asset_auto_fetched(local_path):
            # Remove the asset file
            if local_path.exists():
                local_path.unlink()
                print(f"    🗑 Removed: {local_path.name}")
                removed += 1

            # Remove the marker
            marker = local_path.with_name(local_path.name + MARKER_SUFFIX)
            if marker.exists():
                marker.unlink()

            # Generate placeholder marker
            description = asset.get("description", asset.get("id", ""))
            generate_placeholder_pdf(local_path, description)

        elif is_asset_present(local_path):
            print(f"    ⊘ Kept (manually placed): {local_path.name}")

    return removed


# ---------------------------------------------------------------------------
# Standalone entry point (also importable by pack.py)
# ---------------------------------------------------------------------------

def load_catalog() -> dict:
    """Load and return the CATALOG.json contents."""
    if not CATALOG_PATH.exists():
        print(f"Error: CATALOG.json not found at {CATALOG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch institutional assets (logos, etc.) for apograph templates.",
        epilog="Examples:\n"
               "  python scripts/assets.py                    # fetch all\n"
               "  python scripts/assets.py thesis-polito-msc-latex  # fetch for one\n"
               "  python scripts/assets.py --status            # check status\n"
               "  python scripts/assets.py --clean             # remove auto-fetched\n"
               "  python scripts/assets.py --force             # re-download all\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "template_id",
        nargs="?",
        help="Template ID to fetch assets for (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download assets even if already present",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check the status of all assets",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove auto-fetched assets (preserves manually placed files)",
    )

    args = parser.parse_args()
    catalog = load_catalog()
    templates = catalog.get("templates", [])

    # Filter to a specific template if ID is given
    if args.template_id:
        templates = [t for t in templates if t["id"] == args.template_id]
        if not templates:
            available = [t["id"] for t in catalog.get("templates", [])]
            print(f"Error: template '{args.template_id}' not found.", file=sys.stderr)
            print(f"Available: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)

    # ---- STATUS ----
    if args.status:
        print("Asset status:\n")
        any_assets = False
        for t in templates:
            statuses = check_template_assets(t)
            if not statuses:
                continue
            any_assets = True
            print(f"  [{t['id']}]")
            for s in statuses:
                icon = "✓" if s["present"] else "✗"
                source = f" ({s['source']})" if s["present"] else ""
                url_note = "" if s["has_url"] else " [no URL configured]"
                print(f"    {icon} {s['description']}: {s['local_path']}{source}{url_note}")
            print()

        if not any_assets:
            print("  No templates have assets configured.")
        return

    # ---- CLEAN ----
    if args.clean:
        print("Cleaning auto-fetched assets...\n")
        total_removed = 0
        for t in templates:
            assets = t.get("assets", [])
            if not assets:
                continue
            print(f"  [{t['id']}]")
            removed = clean_template_assets(t)
            total_removed += removed
            print()

        print(f"Removed {total_removed} auto-fetched file(s).")
        print("Manually placed files were preserved.")
        return

    # ---- FETCH ----
    print("Fetching institutional assets...\n")
    totals = {"fetched": 0, "skipped": 0, "failed": 0}

    for t in templates:
        assets = t.get("assets", [])
        if not assets:
            continue
        print(f"  [{t['id']}]")
        result = fetch_template_assets(t, force=args.force)
        for key in totals:
            totals[key] += result.get(key, 0)
        print()

    # Summary
    if totals["fetched"] + totals["skipped"] + totals["failed"] == 0:
        print("No templates have assets configured yet.")
        print("Add 'assets' entries to CATALOG.json to enable dynamic logo fetching.")
    else:
        print(f"Done: {totals['fetched']} fetched, "
              f"{totals['skipped']} already present, "
              f"{totals['failed']} failed")

        if totals["failed"] > 0:
            print("\nFailed downloads will use placeholder boxes in LaTeX.")
            print("Templates will still compile correctly.")


if __name__ == "__main__":
    main()
