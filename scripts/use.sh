#!/usr/bin/env bash
# Thin launcher for Apograph's canonical Python CLI.
#
# Install the canonical client:
#   pipx install apograph-templates
#
# From a repository checkout:
#   bash scripts/use.sh thesis-polito-latex my-thesis

set -euo pipefail

PRODUCT_PREFIX="apograph-templates "
CLI_SPEC="${APOGRAPH_CLI_SPEC:-apograph-templates}"

error() {
    printf 'apograph: error: %s\n' "$*" >&2
}

run_installed() {
    local version_output
    if ! command -v apograph >/dev/null 2>&1; then
        return 1
    fi
    version_output="$(apograph --version 2>/dev/null || true)"
    if [[ "$version_output" != "${PRODUCT_PREFIX}"* ]]; then
        error "an unrelated 'apograph' command is already on PATH; ignoring it"
        return 1
    fi
    exec apograph new "$@"
}

run_checkout() {
    local script_dir repository_root
    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)" \
        || return 1
    repository_root="$(cd -- "${script_dir}/.." >/dev/null 2>&1 && pwd)" \
        || return 1
    if [[ ! -f "${repository_root}/src/apograph_templates/__main__.py" ]]; then
        return 1
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        error "Python 3.10 or newer is required"
        exit 1
    fi
    PYTHONPATH="${repository_root}/src${PYTHONPATH:+:${PYTHONPATH}}" \
        exec python3 -m apograph_templates new "$@"
}

run_pipx() {
    if ! command -v pipx >/dev/null 2>&1; then
        return 1
    fi
    exec pipx run --spec "${CLI_SPEC}" apograph new "$@"
}

run_installed "$@" || true
run_checkout "$@" || true
run_pipx "$@" || true

error "no verified Apograph CLI installation was found"
error "install pipx, then run:"
error "  pipx install apograph-templates"
error "or download a template ZIP directly from the Apograph Releases page"
exit 1
