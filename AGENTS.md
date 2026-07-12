# Repository guidance for coding agents

## Product boundary

Apograph is a curated catalog and release system for self-contained LaTeX and
Typst starter projects. The canonical user product is a tested release artifact,
not a monorepo checkout.

## Required invariants

- Preserve existing user changes and ignored local reference material.
- Never force-add ignored institution branding assets.
- Never describe a `draft` catalog entry as publicly available.
- `CATALOG.json` is the only authored template metadata source.
- Do not add source `template.json` files; they are generated into artifacts.
- Do not claim that a template is official without recorded endorsement.
- Do not infer redistribution rights from public accessibility.
- Do not suppress required validation, compilation, or preview failures.
- Do not make a downloaded artifact depend on monorepo-only paths or settings.
- Do not delete `tmp/` during ordinary cleanup; it contains ignored ingestion
  and reference material owned by the maintainer.

## Generated content

The README section between these markers is generated:

```text
<!-- BEGIN GENERATED:PUBLIC_TEMPLATES -->
<!-- END GENERATED:PUBLIC_TEMPLATES -->
```

Regenerate it with:

```bash
python3 scripts/catalog.py generate-readme
```

## Validation

Before handing off catalog or governance work, run:

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py generate-readme --check
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py
git diff --check
```

For LaTeX changes, additionally compile every affected entry point. Direct
draft compilation may be requested by exact template ID; Phase 2 artifact tests
compile the packed PoliTo showcase in isolation as a mandatory check.

## Scope and generated output

- Keep build output under ignored `out/`, `build/`, or temporary directories.
- Do not commit LaTeX auxiliary files.
- Treat preview PDFs as generated artifacts even when an existing preview is
  temporarily present in the working tree.
- Use small, reviewable changes aligned with one implementation-plan phase.
- Update `docs/IMPLEMENTATION_PLAN.md` and `CHANGELOG.md` when a completed phase
  changes repository contracts.

## Licensing and provenance

Read `docs/licensing.md` and `docs/asset-policy.md` before touching third-party
theme files or institution assets. License uncertainty is a publication blocker;
it is not permission to delete provenance or guess an SPDX expression.
