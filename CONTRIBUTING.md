# Contributing to Apograph

Apograph accepts improvements to its tooling and, once the publication pipeline
is stable, carefully maintained template contributions.

## Before opening a change

1. Read `docs/architecture.md`, `docs/authoring.md`, and
   `docs/asset-policy.md`.
2. Search `CATALOG.json` for an existing or deprecated template ID.
3. Establish the provenance and license of every imported file before copying
   it into the repository.
4. Determine whether institution names, marks, and brand assets may be used and
   redistributed.
5. Start new template entries as `draft`.

## Template contribution requirements

A template contribution identifies:

- a responsible maintainer;
- purpose, variant, format, compiler, and entry points;
- institution relationship (`generic`, `unofficial`, `endorsed`, or `official`);
- upstream authors, URLs, revisions, and licenses;
- every external asset and its policy;
- supported customization boundaries;
- expected compatibility and known limitations.

The label `official` requires evidence of endorsement from the represented
institution. A public source or university logo alone is not endorsement.

## Metadata

Edit only the root `CATALOG.json`. Do not add a `template.json` to a template
source directory. Validate changes with:

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py generate-readme
python3 scripts/catalog.py generate-readme --check
```

## Status promotion

- `draft` records incomplete or unverified work.
- `beta` is usable and documented but may still change.
- `stable` satisfies the complete definition of done in
  `docs/IMPLEMENTATION_PLAN.md`.
- `deprecated` remains available for reproducibility but is no longer
  recommended.

Status promotion is a reviewed change. It must not be used to bypass missing
license, artifact, documentation, or compatibility evidence.

## Pull request expectations

- Keep the change focused.
- Describe upstream and asset evidence explicitly.
- Include validation and compilation results.
- Do not commit generated LaTeX auxiliary files or local institution assets.
- Do not mix unrelated formatting with template changes.
- Update documentation when a public contract changes.

## Reporting problems

When reporting a template issue, include the template ID, Apograph release,
compiler, toolchain version, entry point, and the smallest useful error log.
