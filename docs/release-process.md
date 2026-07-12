# Release process

Apograph currently has no publishable template. This document defines the
initial governance process; Phase 4 will automate it.

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

1. Update the changelog and `release_version`.
2. Run catalog validation and all tests.
3. Build artifacts in a clean release-equivalent checkout.
4. Compile every packed entry point without monorepo-only environment variables.
5. Generate previews, artifact manifests, and SHA-256 checksums.
6. Inspect the candidate file list and notices.
7. Test direct ZIP download and Overleaf import for each LaTeX artifact.
8. Create the protected `v<release_version>` tag.
9. Publish exactly the artifacts that passed candidate verification.
10. Verify every generated release and preview URL after publication.

## Failure behavior

Missing required assets, unresolved license status, compile failures, preview
failures, stale generated documentation, and broken links block publication.
They must not be converted to warnings or hidden with `|| true`.

## Rollback

Do not move a published tag. If artifacts are invalid, document the issue,
remove or mark the release appropriately, fix the problem, and publish a new
version. Preserve previous valid artifacts for reproducibility.
