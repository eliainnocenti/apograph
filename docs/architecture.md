# Architecture

## System boundary

Apograph has four layers:

1. **Catalog:** the authoritative description of templates and publication
   eligibility.
2. **Source:** template projects and centralized reusable modules.
3. **Factory:** validation, packing, compilation, preview, and release tooling.
4. **Surfaces:** README, GitHub Releases, the future static gallery, Overleaf
   actions, native Typst distribution, and an optional future CLI.

The release artifact is the user product. Source-tree convenience must not
become a hidden artifact dependency.

## Data flow

```text
CATALOG.json + template source + shared modules + declared assets
                              |
                              v
                    validate repository
                              |
                              v
                   build isolated artifact
                              |
                              v
                  compile packed entry points
                              |
                              v
               preview + ZIP + manifest + checksum
                              |
                              v
             GitHub Release / README / Pages / Overleaf
```

Phase 1 implements the catalog and governance contracts. Phase 2 implements the
isolated artifact pipeline: `pack.py` delegates to tested internal construction
and compilation modules, and `preview.py` reuses the same compiler API for local
source iteration.

## Source layout

```text
templates/<purpose>/<variant>/<format>/
shared/<format>/
```

Purpose is the human browsing axis. Institution, compiler, format, and maturity
are catalog facets. Variant slugs remain compact and descriptive instead of
creating deeply normalized directory trees.

## Metadata ownership

`CATALOG.json` is authored. `catalog.schema.json` defines its portable shape.
`scripts/catalog.py` enforces repository-specific semantic checks. Public
documentation is generated from validated catalog data.

Artifact `template.json` files are generated snapshots containing catalog data,
release version, source commit, included dependencies/assets, and checksums.
They are not edited in source directories.

## Publication boundary

Only `beta` and `stable` entries are public. Drafts can be compiled directly by
maintainers, but ordinary all-template release operations must eventually skip
them. A stable template satisfies the definition of done in the implementation
plan.

## Shared modules

Centralization applies to source ownership, not runtime delivery. Shared modules
must be small and composable. Template policy—layout, line spacing, headers,
captions, and Beamer behavior—normally remains template-local. Release artifacts
vendor the exact required shared modules.

## Current known gaps

- The PoliTo Beamer beta passes licensing, isolated artifact compilation,
  preview, documentation, and Overleaf TeX Live 2025 import gates.
- The five other template entries are placeholders.
- The compile and release workflows use pinned actions and the canonical
  artifact builder. Clean-runner packed-artifact and unpublished-candidate
  paths passed Gate C on 2026-07-13.

The remaining gaps belong to Phase 5 and later: no public collection release or
static gallery exists yet, and draft templates are intentionally unavailable.
