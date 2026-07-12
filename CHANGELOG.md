# Changelog

All notable changes to Apograph will be documented here. The collection follows
Semantic Versioning while it uses a single global release timeline.

## Unreleased

### Added

- Approved repository implementation plan.
- Machine-readable catalog schema and standard-library validation command.
- Explicit template maturity, provenance, institution relationship, licensing,
  compatibility, entry-point, maintainer, and asset-policy metadata.
- Generated README catalog listing.
- Initial architecture, authoring, asset, licensing, release, contribution, and
  coding-agent guidance.
- Phase 0 dirty-worktree preservation inventory.
- Deterministic artifact builder with root-vendored shared LaTeX modules,
  generated artifact metadata/README/editor files, SHA-256 sidecars, and
  machine-readable build reports.
- Shared isolated compilation primitives and packed PoliTo Beamer integration
  coverage.
- Compiling text/box fallbacks for all PoliTo showcase assets used by the draft.

### Changed

- All current template entries are explicitly classified as drafts.
- The catalog is the only authored metadata source.
- The README no longer presents placeholder directories as released templates.
- `pack.py` now tests the packed artifact itself, preserves legitimate PDFs,
  excludes generated output explicitly, and installs outputs atomically.
- Institution logos/backgrounds remain user-provided and are never downloaded
  by the installer; artifacts document exact optional paths.
- The shell installer refuses non-empty destinations instead of deleting them.

### Removed

- Duplicated source `template.json` files; manifests are generated only inside
  artifacts.
- TeX path rewriting and the install-time asset downloader.

## 0.0.0 — 2026-06-12

- Initial repository skeleton, placeholder template inventory, shared LaTeX
  packages, and development scripts.
