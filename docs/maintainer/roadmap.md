# Maintainer roadmap

This is the active, intentionally compact roadmap. Detailed historical plans
and worktree evidence are preserved locally under `tmp/maintainer/archive/`.

## Completed foundation — Phases 0–5

The repository now has:

- a checkpointed and classified starting worktree;
- a schema-backed catalog with statuses, provenance, assets, and generated
  public listings;
- deterministic self-contained artifacts with root-vendored shared modules;
- isolated source/artifact compilation and regression tests;
- a licensed, attributed, unofficial PoliTo Beamer beta with legal-safe asset
  fallbacks;
- release-candidate assembly, protected-tag publication, immutable versioned
  assets, and CI summary gates.

The first public prerelease is `v0.1.0`.

## Current milestone — Template foundation refactor

- [x] Flatten source paths to `templates/<purpose>/<variant>-<format>/`.
- [x] Keep presentation starter content under `content/` and collapse the
  showcase into one reference file.
- [x] Restore and credit Mattia Ippoliti's original teaching showcase.
- [x] Document precise, authorization-aware acquisition paths for PoliTo
  assets without redistributing them.
- [x] Adapt one PoliTo thesis source for Bachelor and Master modes.
- [x] Restore Luigi De Russis's title-page, Latin Modern typography, document
  flow, package features, and teaching content as the thesis baseline; defer
  optional Poppins support to a separate compatibility profile.
- [x] Consolidate maintainer documentation and remove duplicate release
  narratives.
- [x] Pass catalog, documentation, Python, source compile, and packed-artifact
  validation for the complete refactor.
- [x] Upload and compile the exact PoliTo thesis release-candidate ZIP on
  Overleaf with pdfLaTeX.
- [x] Complete the human licensing review and record the accepted component
  boundary.
- [x] Select `v0.2.0` as the next collection version and include the two verified
  PoliTo beta templates.
- [x] Promote the PoliTo thesis to beta and write the versioned release notes.
- [ ] Verify both exact, CI-built `v0.2.0` ZIPs on Overleaf before creating the
  protected release tag.

The PoliTo thesis is promoted in `v0.2.0`; generated links now target that new
immutable collection rather than the older release. The existing `v0.1.0` links
and tag remain immutable.

## Next milestone — Broaden the tested catalog

Work one template at a time:

1. finish provenance and institutional evidence;
2. create the minimal configuration/content surface;
3. implement legal-safe asset fallbacks;
4. compile source and packed artifact;
5. verify the exact ZIP in Overleaf when claimed;
6. promote only after all beta gates pass.

Likely candidates are the generic academic presentation, UniFi thesis, academic
report, and course-project report. Typst entries should be added only where an
independently useful Typst design exists; format symmetry is not a goal.

## Current product milestone — Apograph CLI

- Implement a dependency-free Python command-line application with `list`,
  `info`, and `new` commands.
- Resolve only published GitHub Release assets through `release-index.json`.
- Verify SHA-256 checksums and extract through a safe, atomic destination flow.
- Keep the shell entry point as a thin convenience launcher.
- Exercise the CLI from its source tree before deciding on PyPI publication.

## Later product milestones

- Generate a small GitHub Pages gallery from `CATALOG.json`, release previews,
  and versioned download/Overleaf links.
- Add migration policy and compatibility promises before any template becomes
  `stable`.
- Consider external contributions and a contribution guide only when the
  project actually opens to routine third-party submissions.
