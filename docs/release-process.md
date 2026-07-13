# Release process

Apograph uses one global collection version. Phase 4 established an unpublished
candidate path; Phase 5 adds a protected tag-publication path for the v0.1.0
prerelease. Creating a candidate never creates a GitHub Release or an entry in
the repository's Releases sidebar. A candidate is a workflow artifact attached
to its Actions run and is subject to that workflow's retention period.

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
- A version-matched file exists under `docs/releases/` and records limitations
  and feedback channels.
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
7. Set `release_version`, set `release_channel`, add the matching release notes,
   and move the matching changelog entry out of `Unreleased`.
8. Configure an active tag ruleset matching `v*`. Restrict tag creation,
   updates, and deletion; keep an explicit repository-admin bypass for the
   maintainer who creates an approved release.
9. Create `v<release_version>` only after candidate approval. The workflow
   rejects a tag when `github.ref_protected` is false.
10. The tag run rebuilds and verifies the candidate, validates tag/catalog/
    changelog agreement, and publishes exactly its own tested output directory.
11. The workflow queries the published release and fails if its prerelease
    state, asset names, upload state, or versioned download URLs differ from the
    catalog-backed expectation.
12. Manually open the README preview, download, and Overleaf actions once.

Development (`-dev`) versions are intentionally rejected by the publication
tag gate. `release_channel: prerelease` maps to GitHub's prerelease flag; it does
not alter the semantic version or filenames.

## Failure behavior

Missing required assets, unresolved license status, compile failures, preview
failures, stale generated documentation, and broken links block publication.
They must not be converted to warnings or hidden with `|| true`.

Candidate metadata assembly also fails on missing or unexpected public-template
reports, developer-mode reports, commit/version mismatches, checksum drift, or
inconsistent source epochs. Publication additionally fails for an unprotected
tag or a GitHub Release whose exact public asset set is wrong.

## Rollback

Do not move a published tag. If artifacts are invalid, document the issue,
remove or mark the release appropriately, fix the problem, and publish a new
version. Preserve previous valid artifacts for reproducibility.
