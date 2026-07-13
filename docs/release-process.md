# Release process

Apograph has one beta template but no published collection release. Phase 4
implemented an unpublished candidate path and a separately gated
tag-publication path; creating a candidate never creates a GitHub Release or an
entry in the repository's Releases sidebar. An unpublished candidate is a
workflow artifact attached to its Actions run and is subject to that workflow's
retention period.

The candidate path was last verified by manual run `29235596362` for commit
`847240b6aba98680c099cce93c03c7399b4f9141`. It produced the catalog snapshot,
ZIP, checksum, preview, build report, and release index and reported
`Published: false`.

## Preconditions

- Catalog and generated documentation are current.
- Every included template is beta or stable.
- Licensing and asset evidence is verified.
- Every publishable entry point compiles from source and from the packed
  artifact.
- Previews are generated from the exact packed artifact.
- Changelog and global release version agree.
- Artifact names are derived from stable template IDs.

## Candidate workflow

1. Run the `Release` workflow manually on the intended commit. This executes
   catalog validation and the complete test suite in a pinned TeX Live 2026
   environment.
2. Build artifacts in release mode with the checked-out full commit SHA.
3. Let `pack.py` compile every entry point from the packed project and derive
   previews from those same results.
4. Let `release.py assemble` verify ZIP and preview hashes, report provenance,
   the complete public-template set, and the shared source epoch.
5. Download the `release-candidate-<sha>` workflow artifact. It contains the
   ZIPs, checksum sidecars, previews, build reports, `CATALOG.json`, and
   `release-index.json` that were tested together.
6. Inspect the candidate file list, notices, and release index. Test direct ZIP
   extraction and Overleaf import for each LaTeX artifact.
7. Update `release_version` and move the matching changelog entry out of
   `Unreleased`.
8. Create the protected `v<release_version>` tag only after candidate approval.
9. The tag run rebuilds and verifies the candidate, validates tag/catalog/
   changelog agreement, and publishes exactly its own tested output directory.
10. Verify every generated release and preview URL after publication.

The current `0.1.0-dev` version is intentionally rejected by the publication
tag gate.

## Failure behavior

Missing required assets, unresolved license status, compile failures, preview
failures, stale generated documentation, and broken links block publication.
They must not be converted to warnings or hidden with `|| true`.

Candidate metadata assembly also fails on missing or unexpected public-template
reports, developer-mode reports, commit/version mismatches, checksum drift, or
inconsistent source epochs.

## Rollback

Do not move a published tag. If artifacts are invalid, document the issue,
remove or mark the release appropriately, fix the problem, and publish a new
version. Preserve previous valid artifacts for reproducibility.
