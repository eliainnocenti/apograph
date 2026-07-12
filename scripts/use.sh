#!/usr/bin/env bash
# ============================================================================
# use.sh — Download and set up an apograph template locally.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/eliainnocenti/apograph/main/scripts/use.sh \
#     | bash -s -- <purpose> <variant> <language> [--out <dir>]
#
# Examples:
#   bash scripts/use.sh thesis polito-msc latex
#   bash scripts/use.sh presentation beamer-academic latex --out ./my-slides
#   curl -fsSL https://raw.githubusercontent.com/.../use.sh | bash -s -- thesis polito-msc latex
#
# Requirements: curl, unzip (available on macOS and most Linux distros)
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_OWNER="eliainnocenti"
REPO_NAME="apograph"
BASE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

info()  { echo -e "${BLUE}ℹ${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*" >&2; }

usage() {
    cat <<EOF
${BOLD}apograph — template installer${NC}

Usage:
  $(basename "$0") <purpose> <variant> <language> [options]

Arguments:
  purpose     Template purpose: thesis, presentation, report
  variant     Template variant: polito-msc, unifi-bsc, beamer-academic, etc.
  language    Template language: latex, typst

Options:
  --out DIR   Output directory (default: ./<variant>)
  --version   Release version tag (default: latest)
  --help      Show this help message

Examples:
  $(basename "$0") thesis polito-msc latex
  $(basename "$0") presentation beamer-academic latex --out ./my-slides

EOF
    exit 0
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

PURPOSE=""
VARIANT=""
LANGUAGE=""
OUT_DIR=""
VERSION="latest"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)
            OUT_DIR="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        -*)
            error "Unknown option: $1"
            usage
            ;;
        *)
            if [[ -z "$PURPOSE" ]]; then
                PURPOSE="$1"
            elif [[ -z "$VARIANT" ]]; then
                VARIANT="$1"
            elif [[ -z "$LANGUAGE" ]]; then
                LANGUAGE="$1"
            else
                error "Too many arguments"
                usage
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PURPOSE" || -z "$VARIANT" || -z "$LANGUAGE" ]]; then
    error "Missing required arguments"
    echo ""
    usage
fi

# Construct the template ID (matches CATALOG.json convention)
TEMPLATE_ID="${PURPOSE}-${VARIANT}-${LANGUAGE}"

# Default output directory
if [[ -z "$OUT_DIR" ]]; then
    OUT_DIR="./${VARIANT}"
fi

# ---------------------------------------------------------------------------
# Download and extract
# ---------------------------------------------------------------------------

echo ""
echo -e "${BOLD}apograph${NC} — setting up ${BLUE}${TEMPLATE_ID}${NC}"
echo ""

# Determine the download URL
if [[ "$VERSION" == "latest" ]]; then
    ZIP_URL="${BASE_URL}/releases/latest/download/${TEMPLATE_ID}.zip"
else
    ZIP_URL="${BASE_URL}/releases/download/${VERSION}/${TEMPLATE_ID}.zip"
fi

info "Template:  ${TEMPLATE_ID}"
info "Version:   ${VERSION}"
info "Output:    ${OUT_DIR}"
info "URL:       ${ZIP_URL}"
echo ""

# Check for required tools
for cmd in curl unzip; do
    if ! command -v "$cmd" &> /dev/null; then
        error "'${cmd}' is required but not installed"
        exit 1
    fi
done

# Check if output directory already exists
if [[ -d "$OUT_DIR" ]]; then
    warn "Directory '${OUT_DIR}' already exists"
    read -rp "Overwrite? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        info "Aborted."
        exit 0
    fi
    rm -rf "$OUT_DIR"
fi

# Create a temporary directory for download
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Download
info "Downloading..."
if ! curl -fsSL -o "${TMP_DIR}/${TEMPLATE_ID}.zip" "$ZIP_URL"; then
    error "Failed to download template"
    error "Check that the template ID and version are correct."
    error "Available templates: ${BASE_URL}#available-templates"
    exit 1
fi
ok "Downloaded"

# Extract
info "Extracting..."
unzip -q "${TMP_DIR}/${TEMPLATE_ID}.zip" -d "${TMP_DIR}/extracted"

# Move to output directory
mkdir -p "$(dirname "$OUT_DIR")"
mv "${TMP_DIR}/extracted" "$OUT_DIR"
ok "Extracted to ${OUT_DIR}"

# ---------------------------------------------------------------------------
# Fetch institutional assets (logos, etc.)
# ---------------------------------------------------------------------------

# Attempt to download assets if the template has a template.json with asset info.
# This requires Python 3 — if not available, skip gracefully.
if command -v python3 &> /dev/null && [[ -f "${OUT_DIR}/template.json" ]]; then
    # Download assets.py to a temp location and run it
    ASSETS_SCRIPT_URL="${BASE_URL}/raw/main/scripts/assets.py"
    ASSETS_SCRIPT="${TMP_DIR}/assets.py"

    info "Checking for institutional assets (logos, etc.)..."
    if curl -fsSL -o "$ASSETS_SCRIPT" "$ASSETS_SCRIPT_URL" 2>/dev/null; then
        # Run the asset fetcher on the template directory
        # Parse template.json to find asset URLs and download them
        python3 -c "
import json, sys, os
sys.path.insert(0, '${TMP_DIR}')

try:
    with open('${OUT_DIR}/template.json') as f:
        meta = json.load(f)

    assets = meta.get('assets', [])
    if not assets:
        sys.exit(0)

    import urllib.request, urllib.error

    for asset in assets:
        url = asset.get('official_url')
        local_path = os.path.join('${OUT_DIR}', asset.get('local_path', ''))
        desc = asset.get('description', 'asset')

        if not url:
            print(f'  ⚠ No URL for {desc} — placeholder will be used')
            continue

        try:
            print(f'  📥 Downloading {desc}...')
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                with open(local_path, 'wb') as out:
                    out.write(resp.read())
            print(f'  ✓ Saved: {os.path.basename(local_path)}')
        except Exception as e:
            print(f'  ⚠ Could not download {desc}: {e}')
            print(f'    Template will compile with a placeholder box.')
except Exception:
    pass  # silently skip if anything fails
" 2>/dev/null || true
    fi
else
    info "Python3 not found — skipping asset download (template will use placeholders)"
fi

# ---------------------------------------------------------------------------
# Success message
# ---------------------------------------------------------------------------

echo ""
echo -e "${GREEN}${BOLD}Done!${NC} Your template is ready at ${BOLD}${OUT_DIR}${NC}"
echo ""
echo "Next steps:"
echo "  1. cd ${OUT_DIR}"
echo "  2. Open in VSCode: code ."
echo "  3. Edit main.tex and start writing"
echo "  4. Compile with: latexmk -pdf main.tex"
echo ""
echo "Tip: For Overleaf, ZIP this folder and upload via"
echo "     New Project → Upload Project."
echo ""
