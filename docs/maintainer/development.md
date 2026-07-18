# Maintainer development guide

This document is the compact engineering contract for Apograph. Historical
planning and worktree records are preserved locally under the ignored
`tmp/maintainer/archive/` tree; they are not public product documentation.

## Product boundary

Apograph is a catalog and release system for self-contained LaTeX and Typst
starter projects. The product a user downloads is a tested, versioned release
artifact—not a source directory copied from the monorepo.

The repository has four layers:

1. `CATALOG.json` is the authored metadata and release policy source.
2. `templates/` contains template source projects.
3. `shared/` contains reusable modules maintained once in the monorepo.
4. `scripts/` validates, compiles, vendors, packs, and publishes artifacts.

## Source layout and identity

Template directories are organized by purpose, with the markup format in the
leaf directory name:

```text
templates/<purpose>/<variant>-<format>/
```

Examples:

```text
templates/presentation/beamer-polito-latex/
templates/thesis/polito-latex/
templates/report/academic-latex/
```

This avoids empty `latex/` or `typst/` siblings and does not imply that every
design exists in both formats. The catalog ID follows
`<purpose>-<variant>-<format>` and remains the stable machine-facing identity.

A source template does not contain `template.json`. The packer generates that
manifest in the downloadable artifact from `CATALOG.json`.

## Catalog ownership

Never duplicate catalog fields in per-template metadata. Each entry records:

- identity, purpose, variant, format, and status;
- institution relationship and requirements evidence;
- compiler and verified compatibility;
- source directory and entry points;
- shared dependencies;
- template license and upstream provenance;
- declared assets, fallbacks, and asset license status;
- readiness notes and maintainer dates.

Use these commands after every metadata edit:

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py generate-readme
python3 scripts/catalog.py generate-readme --check
```

The README section between the generated markers is replaced mechanically.
Do not edit the generated table by hand.

## Status model

- `draft`: inventory or active development; never listed as a download.
- `beta`: publicly downloadable, documented, licensed, and tested, but its
  public interface may still change.
- `stable`: public interface and compatibility promises are intentionally
  maintained.
- `deprecated`: retained for migration/history, with a documented successor or
  retirement path.

Promotion to `beta` requires at least:

- a starter entry point and, when useful, a showcase entry point;
- verified template licensing and complete attribution;
- a declared policy for every asset;
- compilation without user-provided assets;
- an isolated packed-artifact compile;
- a representative generated preview;
- user-facing README instructions;
- an exact-ZIP Overleaf test when Overleaf compatibility is claimed.

`draft` entries may be compiled by exact ID but are excluded from the public
README, default CI matrix, and release asset set.

## Template authoring

Prefer a small user surface:

- `main.tex` or `main.typ` assembles the document;
- `config.tex` or its Typst equivalent contains user metadata and high-level
  switches;
- `content/` contains material users replace;
- `theme/` contains implementation details and optional asset destinations;
- `README.md` explains the concrete workflow and limitations;
- `NOTICE` and `LICENSES/` preserve third-party provenance where required.

Keep showcase material outside the minimal starter's include graph. A compact
single `showcase.tex` is preferred when splitting it would create navigation
noise without helping real authoring.

For adapted work, record the direct upstream source, author, immutable revision
or durable snapshot evidence, license, file relationship, and Apograph
modifications. Public accessibility is not redistribution permission, and an
institution-inspired layout is not official without recorded endorsement.

## Shared modules

Shared LaTeX modules live under `shared/latex/` and are referenced by catalog
path. During a source-tree compile, the compile helper may add `shared/latex/`
to `TEXINPUTS`. During packing, every declared module is copied directly to the
artifact ZIP root. Template code is not rewritten.

Consequences:

- authors maintain one canonical shared module;
- a downloaded project has no monorepo dependency;
- Overleaf and ordinary local compilers see the packages immediately;
- an undeclared or missing dependency is a hard packing failure.

Shared modules must stay class-neutral unless their scope explicitly names the
consuming class. Compatibility tests compile them in the document classes they
claim to support.

## Asset contract

All assets are declared in `CATALOG.json`. The supported modes and evidence
requirements are defined in [the asset policy](../asset-policy.md).

Institution logos default to `user-provided`. Such a file:

- is ignored by Git;
- is never copied implicitly from a maintainer's machine;
- has an exact destination path documented in the artifact;
- must have a compiling fallback when optional;
- cannot use `source_url` as a disguised download hint.

Human-readable acquisition guidance may link to an official policy or describe
a private portal. It must distinguish “where an authorized user can obtain the
file” from “permission to redistribute the file.”

## Artifact contract

`scripts/pack.py` builds a canonical artifact in a temporary workspace and
publishes outputs only after every requested step succeeds. Release-mode builds
require a clean, verified source commit. Outputs are deterministic for the same
source inputs and source date.

A public template build produces:

```text
<template-id>.zip
<template-id>.zip.sha256
<template-id>.build.json
<template-id>.preview.pdf
```

Inside the ZIP, the project source is at root together with declared shared
modules, generated `template.json`, generated `APOGRAPH.md`, license/provenance
files, and optional VS Code configuration. Generated PDFs, auxiliaries, ignored
assets, undeclared theme files, and repository-only paths are excluded.

Useful commands:

```bash
python3 scripts/pack.py <template-id>
python3 scripts/pack.py <template-id> --force
python3 scripts/pack.py --all --mode release --source-commit <commit>
python3 scripts/preview.py <template-id>
```

`preview.py` is a source-tree convenience. The release gate compiles the
packed, extracted artifact in isolation with repository search paths removed.

## Validation and compilation

Before handoff, run:

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py generate-readme --check
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py
git diff --check
```

Compile every changed LaTeX entry point. For a public template, also build the
canonical artifact and verify its extracted starter/showcase without optional
assets. CI repeats catalog discovery, Python tests, source compilation, packed
artifact compilation, release assembly, and a required summary gate.

Never suppress a validation, compilation, or preview failure to make the
pipeline green. Preserve compiler output for diagnosis and keep generated files
under ignored `out/`, `build/`, or temporary directories.

## Release process

`CATALOG.json` owns `release_version` and `release_channel`. The only authored
release narrative is:

```text
docs/releases/v<release_version>.md
```

Its top-level heading must begin `# Apograph v<release_version>`. The release
validator requires that file, checks the heading against the catalog/tag, and
passes the same path to GitHub as the Release body. There is no separate
changelog to synchronize.

Release sequence:

1. finish template, catalog, documentation, licensing, and compatibility gates;
2. choose the next version and add its versioned release-note file;
3. regenerate the README and run the complete validation suite;
4. run the release-candidate workflow from the exact source commit;
5. inspect its catalog, ZIP, checksum, build report, preview, and release index;
6. create the protected `v<release_version>` tag at that exact commit;
7. let the tag workflow rebuild/verify and publish the GitHub Release;
8. verify the published asset set and links.

Tags and published artifacts are immutable. Corrections receive a new version.
A manually triggered candidate build uploads an Actions artifact only; it does
not create an entry in GitHub's Releases page.

## Documentation boundary

Public documentation is intentionally small:

- `README.md` for discovery and use;
- `docs/asset-policy.md` and `docs/licensing.md` for repository-wide policy;
- `docs/releases/` for immutable release narratives;
- `docs/maintainer/development.md` and `roadmap.md` for active maintenance.

Long-form historical plans and worktree inventories belong under ignored
`tmp/maintainer/archive/`. Preserve them locally; do not make CI depend on them.
