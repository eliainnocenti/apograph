# =============================================================================
# Apograph — Makefile
#
# Convenience wrapper around Python scripts for common operations.
# Run `make help` to see all available targets.
# =============================================================================

.PHONY: help pack pack-all preview preview-one clean list

# Default target
help: ## Show this help message
	@echo ""
	@echo "  apograph — LaTeX & Typst template library"
	@echo ""
	@echo "  Usage: make <target> [options]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Examples:"
	@echo "    make pack ID=thesis-polito-msc-latex"
	@echo "    make pack-all"
	@echo "    make preview"
	@echo "    make pack ID=thesis-polito-msc-latex VSCODE=1"
	@echo ""

# ---------------------------------------------------------------------------
# Packing (bundle templates into self-contained ZIPs)
# ---------------------------------------------------------------------------

pack: ## Pack a single template into a ZIP (requires ID=<template-id>)
ifndef ID
	$(error ID is required. Usage: make pack ID=thesis-polito-msc-latex)
endif
	@python3 scripts/pack.py $(ID) $(if $(VSCODE),--vscode,) $(if $(OUT),--out $(OUT),)

pack-all: ## Pack all templates into ZIPs
	@python3 scripts/pack.py --all $(if $(VSCODE),--vscode,) $(if $(OUT),--out $(OUT),)

# ---------------------------------------------------------------------------
# Preview (compile templates and generate preview PDFs)
# ---------------------------------------------------------------------------

preview: ## Compile all templates and generate preview PDFs
	@python3 scripts/preview.py

preview-one: ## Compile a single template (requires ID=<template-id>)
ifndef ID
	$(error ID is required. Usage: make preview-one ID=thesis-polito-msc-latex)
endif
	@python3 scripts/preview.py $(ID)

# ---------------------------------------------------------------------------
# Institutional Assets (logos, etc.)
# ---------------------------------------------------------------------------

fetch-assets: ## Fetch institutional assets (logos, etc.) from official servers
	@python3 scripts/assets.py

status-assets: ## Check status of institutional assets
	@python3 scripts/assets.py --status

clean-assets: ## Remove downloaded assets (preserves manual ones)
	@python3 scripts/assets.py --clean

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

list: ## List all available templates
	@python3 scripts/preview.py --list

clean: ## Remove build artifacts (build/, *.zip, out/ dirs, LaTeX aux files)
	@echo "Cleaning build artifacts..."
	@rm -rf build/
	@find . -type d -name "out" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.aux" -o -name "*.log" -o -name "*.toc" \
		-o -name "*.lof" -o -name "*.lot" -o -name "*.fls" \
		-o -name "*.fdb_latexmk" -o -name "*.synctex.gz" \
		-o -name "*.bbl" -o -name "*.blg" -o -name "*.bcf" \
		-o -name "*.run.xml" -o -name "*.out" -o -name "*.nav" \
		-o -name "*.snm" -o -name "*.vrb" | xargs rm -f 2>/dev/null || true
	@echo "Done."

clean-previews: ## Remove all template preview PDFs (tracked in Git)
	@echo "Cleaning preview PDFs..."
	@find templates -name "preview.pdf" -exec rm -f {} + 2>/dev/null || true
	@echo "Done."
