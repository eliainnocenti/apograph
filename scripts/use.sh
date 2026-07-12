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

# Never remove a user-selected directory. An existing empty directory is safe;
# a non-empty destination requires the user to choose another path or clean it.
if [[ -d "$OUT_DIR" ]] && [[ -n "$(find "$OUT_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    error "Output directory '${OUT_DIR}' is not empty"
    error "Choose another --out path or empty it yourself after reviewing its contents."
    exit 1
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
mkdir -p "$OUT_DIR"
cp -R "${TMP_DIR}/extracted/." "$OUT_DIR/"
ok "Extracted to ${OUT_DIR}"

# Institution marks classified as user-provided are intentionally not fetched.
# Their exact destination paths and compiling fallbacks are documented in the
# artifact README and template.json.

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
