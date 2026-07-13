# Changelog

All notable changes to Apograph will be documented here. The collection follows
Semantic Versioning while it uses a single global release timeline.

## Unreleased

## 0.1.0 — 2026-07-13

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
- A validated, locally testable catalog-to-CI matrix command for GitHub Actions.
- Release-candidate validation and indexing for ZIPs, previews, checksum
  sidecars, build reports, source commits, catalog snapshots, and source epochs.
- Clean-runner Gate C evidence and an unpublished six-file release candidate for
  the first beta template.
- Versioned preview, ZIP, checksum, and one-click Overleaf actions generated
  from the catalog's collection version.
- Catalog-backed prerelease metadata, protected-tag validation, exact
  post-publication asset verification, v0.1.0 release notes, and a structured
  template-problem issue form.
- Local, VS Code, and Overleaf onboarding plus explicit beta limitations and
  artifact provenance in public and per-template documentation.

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
- The compile workflow no longer embeds quote-sensitive Python inside a shell
  string; it consumes the tested catalog matrix command instead.
- Compile and release workflows now pin all actions, run the canonical artifact
  builder in TeX Live 2026, upload the exact tested candidate, and keep manual
  candidates separate from tag-triggered publication.
- TeX Live container jobs explicitly trust only the mounted GitHub workspace
  for release-mode Git verification, and checkout now uses its pinned Node 24
  release.
- Artifact delivery staging now lives on the selected output filesystem, so
  atomic publication also works when CI mounts the workspace separately from
  `/tmp`.
- Candidate uploads now use the fully pinned Node 24-based
  `actions/upload-artifact` v7.0.1 release.
- The collection version is now `0.1.0` with the `prerelease` channel; public
  artifacts record the version and exact source commit in generated guidance.

### Removed

- Duplicated source `template.json` files; manifests are generated only inside
  artifacts.
- TeX path rewriting and the install-time asset downloader.

## 0.0.0 — 2026-06-12

- Initial repository skeleton, placeholder template inventory, shared LaTeX
  packages, and development scripts.
