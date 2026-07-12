# Phase 0 worktree inventory

Inventory date: 2026-07-12  
Baseline branch: `main`  
Baseline commit: `e8e2c8e911c26aa963e03d5c798c7e4c9c0abe96`

This inventory classifies the dirty worktree that existed before Phase 1 of the
Apograph implementation plan. It is a preservation record, not a declaration
that every file is ready for release.

## Safe checkpoint

Creating the planned `codex/phase-0-1` Git branch was not approved, so Phase 0
did not modify Git metadata, stage files, or create a commit. As a non-destructive
fallback, the complete working directory (excluding `.git`, generated `out/`,
Python bytecode, and `.DS_Store`) was archived before Phase 1 edits. The verified
archive was copied into the repository's existing ignored reference area:

- archive: `tmp/checkpoints/apograph-phase0-checkpoint-20260712.tar.gz`
- temporary duplicate: `/tmp/apograph-phase0-checkpoint-20260712.tar.gz`
- size: 43,440,923 bytes
- SHA-256: `1bc6816b8cf30ee1e88da84efc2b9984c22dacd76c650c8afed7d8a808659ff3`

The archive includes ignored `tmp/` reference material, the local institution
images, the generated preview, all source changes, and the two Phase 0 documents
as they existed at checkpoint time. The ignored workspace copy is durable across
ordinary tasks but is not backed up by Git; a Git checkpoint remains recommended
after review.

## Intended source work

The following existing modifications form one coherent in-progress change:
move institution branding assets from user-content `figures/` directories into
template-owned `theme/assets/` directories and develop the PoliTo Beamer theme.

### Modified tracked files

- `.gitignore`: ignores institution branding files in `theme/assets/` while
  retaining `.gitkeep` and placeholder instructions.
- `CATALOG.json`: moves logo destinations into `theme/assets/` and initially
  declared three assets used by the PoliTo Beamer theme. Phase 2 additionally
  declared the alternative and negative backgrounds discovered by isolated
  artifact compilation.
- `scripts/assets.py`: updates the default asset location and removes stale
  placeholder markers when the real asset exists.
- `scripts/use.sh`: whitespace-only end-of-file cleanup.
- `shared/latex/apograph-polito.sty`: moves the expected logo path to
  `theme/assets/polito-logo.pdf`.
- `shared/latex/apograph-unifi.sty`: moves the expected logo path to
  `theme/assets/unifi-logo.pdf`.
- `templates/presentation/beamer-polito/latex/main.tex`: replaces the three-line
  draft with a compiling theme demonstration split into sections.
- `templates/presentation/beamer-polito/latex/figures/.gitkeep`: empty-file
  normalization associated with the asset move.

### Deleted tracked placeholders

These placeholders were moved, not intentionally discarded:

- `templates/presentation/beamer-polito/latex/figures/polito-logo.pdf.placeholder`
- `templates/thesis/polito-msc/latex/figures/polito-logo.pdf.placeholder`
- `templates/thesis/unifi-bsc/latex/figures/unifi-logo.pdf.placeholder`

### Untracked source files to preserve

- `templates/presentation/beamer-polito/latex/sections/01-introduction.tex`
- `templates/presentation/beamer-polito/latex/sections/02-getting-started.tex`
- `templates/presentation/beamer-polito/latex/sections/03-colors-styles.tex`
- `templates/presentation/beamer-polito/latex/sections/04-layout-elements.tex`
- `templates/presentation/beamer-polito/latex/sections/05-custom-boxes.tex`
- `templates/presentation/beamer-polito/latex/sections/06-diagrams-tables.tex`
- `templates/presentation/beamer-polito/latex/sections/07-special-slides.tex`
- `templates/presentation/beamer-polito/latex/theme/beamerthemesintef.sty`
- `templates/presentation/beamer-polito/latex/theme/sintefcolor.sty`
- the `.gitkeep` and `.placeholder` files under each new `theme/assets/`
  directory.

The theme header identifies the file as derived from the SINTEF Beamer theme and
names CC BY 4.0 and GPL v3. The exact inbound license chain and the requirements
for the local derivative still require evidence review before publication.

## Governance work created before the checkpoint

- `docs/IMPLEMENTATION_PLAN.md`: the approved implementation roadmap.
- `docs/WORKTREE_INVENTORY.md`: this preservation and classification record.

## Generated files

These files are outputs, not authored template source:

- `templates/presentation/beamer-polito/preview.pdf` — generated preview,
  7,633,777 bytes at inventory time; current SHA-256
  `a51e3b1f5df07c502a71ce4d9402a81d54a54fe079fe31eaf9b31192966a878b`.
- `templates/presentation/beamer-polito/latex/out/` — ignored LaTeX auxiliary
  files and compiled PDF.
- `scripts/__pycache__/` — ignored Python bytecode.
- `.DS_Store` files — ignored operating-system metadata.

The preview is preserved in the local checkout but should eventually be
generated and published by CI rather than treated as a hand-authored source
file. It is included in the source checkpoint because it was an existing
untracked, explicitly unignored work product; Phase 1 does not delete or move
it.

## Ignored local institution assets

The following images exist locally under
`templates/presentation/beamer-polito/latex/theme/assets/` and are intentionally
not added to Git until redistribution and attribution evidence is established:

| File | Bytes | SHA-256 |
|---|---:|---|
| `logo_RGB.png` | 181657 | `bfef7c477e561bdc3f156c7aaf95c16bf8e7dfbe588e833dd64f59ee19f88323` |
| `Logo_RGB_negative.png` | 440913 | `9e0948c033627a139e5d6b81693d072006fd9b1f86f488965524c85c0342e47c` |
| `logo_RGB_master.png` | 62526 | `8730591d02905fab80aae1335481f0c720d974fa58dd6b4a57dcb8928be3253a` |
| `logo_RGB_negative_master.png` | 62551 | `97fbc8b36cba0fbda9ec882f1de1232b512510ef57a567e2972f29c63b27c868` |
| `background.png` | 244701 | `7ac888e397a41cac5dbcfa5976fc35241e9a34afbbcfb85306c800c9a8279f87` |
| `background_alternative.png` | 5660778 | `50b6db3945c11fe07faa377ab35c4f2ed3c5c0cabc696385b8484627a38e6698` |
| `background_negative.png` | 223392 | `1e1d4080ec24895eb283f245c5f98b85dee0ffea345274ce01752b51c04b8849` |

The current local packer includes these ignored files when they exist. A clean
CI checkout does not contain them. This is a known Phase 2 artifact-pipeline
problem; Phase 1 only records it.

## Ignored reference and ingestion material

- `tmp/` contains 69 MB of imported source archives, extracted third-party
  templates, examples, PDFs, and a previous interactive design document.

This material remains local and ignored. It is evidence/input for future
template work, not part of the repository or a release. No Phase 0 or Phase 1
operation deletes or relocates it.

## Baseline verification

The following checks were run before the checkpoint:

- `python3 -m py_compile scripts/assets.py scripts/pack.py scripts/preview.py` —
  passed.
- `python3 scripts/preview.py presentation-beamer-polito-latex` — passed.
- `python3 scripts/pack.py presentation-beamer-polito-latex --no-assets ...` —
  passed and produced a 6,813,497-byte local ZIP.
- The five other catalog entries contain only three- or four-line placeholder
  `main.tex` files and are not usable publishable templates.
- `git diff --check` — passed.

## Preservation rules for subsequent phases

- Do not delete, overwrite, or force-add the ignored institution images.
- Do not delete `tmp/` as part of ordinary repository cleanup.
- Preserve the PoliTo theme and section source until its Phase 3 migration.
- Treat the preview and `out/` as reproducible generated outputs, but do not
  remove the existing local preview in Phase 1.
- Do not describe the five placeholder entries as publicly available templates.
