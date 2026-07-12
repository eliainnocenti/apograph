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
- A separate minimal PoliTo Beamer starter, user configuration surface,
  feature-rich showcase entry point, source README, and attribution notice.
- Complete GPL-3.0 and CC-BY-4.0 component license texts for the PoliTo artifact.
- Maintainer approval of the PoliTo GPL/CC-BY component boundary, attribution,
  modification record, and non-endorsement statements.
- Class-compatibility fixtures for shared LaTeX modules across article, report,
  book, and Beamer.
- Exact-ZIP Overleaf verification for both PoliTo entry points using pdfLaTeX
  and TeX Live 2025.

### Changed

- Placeholder entries remain drafts; PoliTo Beamer is the first beta entry.
- The catalog is the only authored metadata source.
- The README no longer presents placeholder directories as released templates.
- `pack.py` now tests the packed artifact itself, preserves legitimate PDFs,
  excludes generated output explicitly, and installs outputs atomically.
- Institution logos/backgrounds remain user-provided and are never downloaded
  by the installer; artifacts document exact optional paths.
- The shell installer refuses non-empty destinations instead of deleting them.
- Shared math and typography modules now contain class-neutral primitives;
  optional namespaced theorem environments live in `apograph-theorems.sty`.
- The PoliTo theme exposes namespaced commands and opt-in section/subtitle
  behavior while retaining compiling user-provided-asset fallbacks.
- The PoliTo artifact records successful isolated starter/showcase compilation
  with TeX Live 2026 and zero-diagnostic Overleaf TeX Live 2025 compilation.
- Starter content now lives only under `content/`; preview-only source is
  isolated under `showcase/` so users see one document-authoring surface.

### Removed

- Duplicated source `template.json` files; manifests are generated only inside
  artifacts.
- TeX path rewriting and the install-time asset downloader.

## 0.0.0 — 2026-06-12

- Initial repository skeleton, placeholder template inventory, shared LaTeX
  packages, and development scripts.
