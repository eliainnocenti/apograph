# Apograph implementation plan

Status: approved architecture, ready for execution  
Last updated: 2026-07-13

Execution progress:

- Phase 0 completed on 2026-07-12 with a filesystem checkpoint; the preferred
  Git branch/commit checkpoint was recorded with the Phase 1 foundation.
- Phase 1 completed on 2026-07-12; catalog, validation, generated listing, and
  initial governance contracts are implemented and verified.
- Phase 2 completed on 2026-07-12; deterministic artifacts, root-vendored shared
  modules, isolated compilation, asset fallbacks, and Gate A tests are implemented.
- Phase 3 completed on 2026-07-12. The starter/showcase/config/theme split,
  component notices, shared-class fixtures, clean TeX Live 2026 artifact
  compilation, maintainer license review, and exact-ZIP Overleaf TeX Live 2025
  verification are recorded; PoliTo Beamer is the first beta entry.
- Phase 4 completed on 2026-07-13. Compile run `29235231851` passed catalog,
  Python, source, packed-artifact, upload, and summary gates from a clean GitHub
  runner. Manual Release run `29235596362` built one unpublished candidate for
  commit `847240b6aba98680c099cce93c03c7399b4f9141`, uploaded the complete six-file
  candidate set, reported `Published: false`, and created no GitHub Release.

## 1. Product definition

Apograph is a curated, versioned catalog and release system for self-contained
LaTeX and Typst starter projects. It is not initially:

- a general document framework;
- a runtime package manager;
- a universal marketplace for university templates;
- a public Python library;
- an automatic updater for documents already created from a template.

The canonical user product is an immutable, self-contained template artifact.
The source monorepo, shared modules, scripts, CI, website, and any future CLI
exist to produce, validate, document, discover, and download those artifacts.

### Primary users

1. A student or colleague who wants to start writing with minimal setup.
2. A local LaTeX or Typst user working in VS Code or another editor.
3. An Overleaf or Typst web-app user who does not want to use a terminal.
4. The maintainer, who needs one source of truth and repeatable releases.
5. A future contributor adding a template for another institution or purpose.

### Product-level success criteria

- A visitor can identify a suitable template in under one minute.
- A visitor can start it locally or online in at most a few actions.
- Every published ZIP compiles outside the Apograph repository.
- A clean checkout and a maintainer's machine produce equivalent artifacts.
- A template never depends on ignored or undeclared local files.
- Catalog data, documentation, CI matrices, and release names cannot silently
  drift apart.
- Licensing, attribution, institution status, and asset redistribution policy
  are visible before a template is published.
- Advanced customization is possible without making the default starter hard to
  understand.

## 2. Approved architectural decisions

### AD-01: purpose-first source layout

Keep the existing high-level structure:

```text
templates/<purpose>/<variant>/<language>/
```

`purpose` is the primary browsing axis. Institution, degree, markup language,
compiler, and tags are catalog facets. Avoid deeper normalization unless a real
collision appears.

### AD-02: curated scope

Apograph starts as a curated collection. Additional institutions are welcome
only after the contribution and maintenance contract exists. A template must
not be labelled `official` unless the represented institution has endorsed it.

### AD-03: centralized source, vendored distribution

Shared modules have one source in `shared/`. The artifact builder copies the
exact required modules into each release. Released projects have no runtime
dependency on the monorepo, `TEXINPUTS`, a network connection, or Apograph.

### AD-04: GitHub Release ZIPs are canonical

README links, the website, the shell helper, Overleaf buttons, and any future
CLI all resolve to the same immutable release artifacts.

### AD-05: no public Python package yet

Python remains an internal implementation language. A public `apograph` CLI is
introduced only when discovery, diagnostics, provenance, or cross-platform
initialization justify its maintenance cost.

### AD-06: website before full CLI

After the release foundation is stable, prioritize a small static gallery over
a feature-rich CLI. The expected audience benefits more from visual discovery,
direct downloads, and one-click Overleaf links.

### AD-07: snapshot update model

A generated project is a versioned snapshot. Apograph records its provenance
but does not modify it automatically. Update checks or Copier-style upgrades
are a later, separately evaluated feature.

### AD-08: native Typst distribution

Typst templates participate in the Apograph catalog and release process. Mature
Typst templates should additionally use Typst Universe and `typst init` instead
of depending on an Apograph-only installer.

### AD-09: global collection version initially

Use one SemVer release for the collection. Keep the catalog schema version and
template maturity status separate. Do not introduce independent per-template
release timelines until the collection is large enough to require them.

## 3. Target repository shape

```text
.
├── AGENTS.md
├── CATALOG.json
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── LICENSES/
│   ├── GPL-3.0-or-later.txt
│   └── CC-BY-4.0.txt
├── Makefile
├── README.md
├── catalog.schema.json
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── architecture.md
│   ├── asset-policy.md
│   ├── authoring.md
│   ├── catalog-reference.md
│   ├── licensing.md
│   └── release-process.md
├── scripts/
│   ├── apograph/
│   │   ├── __init__.py
│   │   ├── artifacts.py
│   │   ├── assets.py
│   │   ├── catalog.py
│   │   ├── compile.py
│   │   └── documentation.py
│   ├── assets.py
│   ├── catalog.py
│   ├── pack.py
│   ├── preview.py
│   ├── release.py
│   └── use.sh
├── shared/
│   ├── latex/
│   │   ├── apograph-colors.sty
│   │   ├── apograph-math-core.sty
│   │   ├── apograph-theorems.sty
│   │   ├── apograph-brand-polito.sty
│   │   └── apograph-brand-unifi.sty
│   └── typst/
├── templates/
│   └── <purpose>/<variant>/<language>/
└── tests/
    ├── fixtures/
    ├── test_artifacts.py
    ├── test_assets.py
    └── test_catalog.py
```

The internal `scripts/apograph/` module is not a public package. It only avoids
duplicating catalog, artifact, and compile logic across script entry points.

## 4. Template contract

Each template language directory follows a predictable contract. Files that do
not apply may be omitted.

```text
latex/
├── main.tex                 # minimal starter entry point
├── showcase.tex             # optional rich preview/demo entry point
├── config.tex               # common user-editable metadata and options
├── bibliography.bib
├── content/                 # chapters, sections, or slides
├── showcase/                # optional support files used only by showcase.*
├── figures/                 # user content assets
├── theme/                   # template-specific implementation
│   └── assets/              # declared template/brand assets only
├── README.md
├── NOTICE                   # template-specific attribution when needed
├── latexmkrc                # only when compiler/main-file configuration needs it
└── .vscode/                 # small, generated, non-user-specific adapter
```

### Entry-point roles

The catalog supports an array instead of one `main_file`:

- `starter`: the file users should edit first;
- `showcase`: a richer document used for previews and visual regression checks;
- `companion`: a related output such as course-project slides;
- `test`: an internal fixture not included in user artifacts.

Each publishable template must have exactly one `starter`. It may have multiple
companion entry points.

### Customization tiers

1. **Immediate:** edit `config.tex` or the arguments in `main.typ`.
2. **Documented:** use supported class/package/function options.
3. **Advanced:** modify the template-local `theme/` implementation.

Do not encode every visual choice as an installer question. Prefer useful
defaults, documented options, and visible `TODO` markers in the starter.

## 5. Catalog contract

`CATALOG.json` is the only authored metadata source. Per-template
`template.json` files are generated into release artifacts and are not stored in
template source directories.

### Root fields

- `schema_version`: version of `catalog.schema.json`.
- `release_version`: current collection version or next development version.
- `repository`: canonical repository metadata.
- `templates`: catalog entries.

### Required template fields

- `id`: stable lowercase identifier; never reuse a retired ID.
- `name`, `description`.
- `purpose` and `variant`.
- `format`: `latex` or `typst`.
- `status`: `draft`, `beta`, `stable`, or `deprecated`.
- `source_dir`.
- `entrypoints`.
- `compiler` and compatibility data.
- `institution`, including `relationship`:
  `generic`, `unofficial`, `endorsed`, or `official`.
- `license`: SPDX expression where possible.
- `upstream`: source URLs, revisions, authors, and modification notes.
- `shared_deps`.
- `assets`.
- `tags`.
- `maintainers`.

### Generated artifact fields

The artifact's `template.json` additionally records:

- Apograph release version;
- source commit SHA;
- catalog schema version;
- build timestamp;
- included shared dependencies and their versions/checksums;
- asset modes and checksums;
- per-file checksums and the name of the external ZIP checksum sidecar (the ZIP
  cannot contain its own checksum without a circular definition);
- supported compiler and entry points.

Release and preview URLs must be generated from the repository, release, and
template ID. Do not manually repeat them in every catalog entry.

### Status semantics

- `draft`: source inventory only; omitted from user-facing downloads.
- `beta`: usable, documented, and compiling; interfaces may still change.
- `stable`: all publication gates pass and compatibility is supported.
- `deprecated`: still available for reproducibility but hidden from default
  recommendations and accompanied by a replacement or reason.

## 6. Shared-module contract

Shared modules must be small, namespaced, composable, and safe across every
declared consuming document class.

### Keep shared

- generic color primitives;
- math operators, paired delimiters, and namespaced commands;
- opt-in theorem helpers that do not assume a `chapter` counter;
- small engine compatibility helpers;
- brand tokens that have documented provenance.

### Keep template-local

- page geometry and aspect ratios;
- line spacing;
- caption, header, footer, and chapter policy;
- Beamer frame and navigation behavior;
- package bundles chosen only for a particular template;
- template-specific composition of logos and backgrounds.

### Artifact layout decision

For LaTeX artifacts, copy required shared `.sty` files into the ZIP root. This
allows bare `\usepackage{apograph-...}` and internal `\RequirePackage` calls to
work in local LaTeX and Overleaf without recursive search configuration. The
files are namespaced, so root-level collision risk is low.

Source-tree compilation may continue to use `TEXINPUTS`. Artifact compilation
must never use it.

## 7. Asset and branding policy

Every declared asset has one mode:

- `bundled`: legally redistributable and committed;
- `fetched`: downloaded from a stable authorized source, with an expected
  checksum and documented license;
- `user-provided`: cannot be redistributed; artifact contains instructions and
  a compiling fallback;
- `generated`: produced during the build from repository-owned inputs;
- `placeholder`: no external file is required and the theme renders a fallback.

Each asset records:

- logical ID and description;
- local destination;
- mode;
- required/optional status;
- source URL where applicable;
- expected checksum where applicable;
- copyright/license/trademark note;
- fallback behavior.

### Rules

- A release must not opportunistically include ignored local assets.
- A release must not fetch an asset with an empty or unverified URL.
- A stable template must compile when every `user-provided` asset is absent.
- The builder must not exclude all PDFs; PDF inclusion is determined by exact
  build-output rules and catalog asset declarations.
- Local and CI builds use the same asset policy.
- Institution names and marks remain attributed to their owners, with an
  explicit non-endorsement statement for unofficial templates.

## 8. Licensing and provenance workstream

This workstream blocks public stable releases but should not block internal
refactoring.

### Tasks

1. Inventory every non-original theme, class, style, image, font, and substantial
   source excerpt.
2. Record upstream author, URL, revision/date, original license, and local
   modifications.
3. Determine the license of the PoliTo Beamer derivative and include the full
   required license and attribution text.
4. Separate the MIT license for original Apograph tooling from template-level
   third-party licenses.
5. Add `LICENSES/`, `docs/licensing.md`, and per-template `NOTICE` files.
6. Determine whether each university logo/background may be redistributed.
7. If redistribution is uncertain, switch it to `user-provided` or a text-only
   placeholder until permission is documented.
8. Add automated catalog checks requiring provenance for non-original and
   institution-branded templates.

### Gate L

- No unknown license remains in a beta/stable artifact.
- Every redistributed third-party file is covered by a recorded license.
- Required attribution ships inside the artifact.
- Institution relationship and trademark disclaimer are accurate.

This is an engineering release gate, not a substitute for legal advice.

## 9. Artifact builder redesign

Refactor `pack.py` around a single tested artifact-building API.

### Required behavior

1. Load and validate the catalog before touching output.
2. Resolve a template by its exact stable ID.
3. Reject `draft` templates in release mode.
4. Copy source files using explicit ignore rules for generated output rather
   than broad extension bans.
5. Exclude `out/`, auxiliary TeX files, local caches, and source-only showcase
   files only when the catalog says they are not part of the artifact.
6. Resolve and copy the complete shared dependency set.
7. Copy shared LaTeX packages to the artifact root.
8. Apply the asset policy deterministically.
9. Generate `template.json`, `README.md` fragments, editor adapters, and any
   required `latexmkrc`.
10. Validate that the starter exists at the ZIP root and all declared entry
    points exist.
11. Compile every publishable entry point from the temporary artifact directory
    without monorepo environment variables.
12. Generate the preview from the packed showcase/starter, not from source.
13. Create a deterministic ZIP: sorted file order, normalized paths and
    permissions, and normalized timestamps.
14. Emit SHA-256 checksums and a machine-readable build report.
15. Leave the temporary artifact available only on requested debug failure.

### Safety behavior

- Refuse to overwrite a non-empty destination unless an explicit safe option is
  given.
- Never invoke `rm -rf` on a user-provided path as a normal control flow.
- Never interpolate shell paths into generated Python code.
- Never silently ignore missing shared dependencies or required assets.
- Warnings are allowed only for explicitly optional data.

### Developer and release modes

- Developer mode may build current tracked-file modifications for iteration.
- Release mode builds from the checked-out commit and fails on relevant
  untracked files or catalog drift.
- Both modes use the same dependency, asset, and compile logic.

### Gate A

- Every beta/stable ZIP compiles in an isolated temporary directory.
- The packed artifact is the input used to generate its preview.
- Two builds of the same commit and toolchain produce identical file lists and
  checksums.
- A clean checkout and a developer checkout without optional local assets
  produce equivalent release artifacts.

## 10. Compilation and preview system

Unify source, artifact, and preview compilation through one internal module.

### LaTeX

- Support pdfLaTeX, LuaLaTeX, and XeLaTeX explicitly.
- Compile with `latexmk`, non-interactive errors, SyncTeX only for local
  development, and isolated output directories.
- Treat warnings according to a documented policy; missing references in a
  showcase should fail stable publication after the required number of passes.
- Test supported TeX Live versions, including the version currently used by
  Overleaf when practical.
- Compile all starter, showcase, and companion entry points declared publishable.

### Typst

- Compile with a pinned supported Typst version.
- Ensure local and web-app-compatible imports.
- Produce PDF and thumbnail previews.

### Previews

- Do not commit auxiliary build directories.
- Prefer generated preview PDFs and thumbnails as CI/Pages/release artifacts.
- Use stable filenames derived solely from the template ID:
  `<id>-preview.pdf` and `<id>-preview.png`.
- Record the source entry point and compiler in preview metadata.

## 11. Catalog validation and tests

Create a fast standard-library validation command:

```bash
python3 scripts/catalog.py validate
```

### Validation checks

- JSON schema validity;
- unique IDs;
- legal status, format, compiler, purpose, and institution values;
- source and entry-point existence;
- one starter entry point;
- valid shared dependency paths and no duplicate dependency IDs;
- valid asset modes and required metadata;
- provenance and license requirements by status;
- generated release filename consistency;
- no checked-in per-template `template.json` duplicates;
- no draft template in public generated documentation;
- no stale generated README/catalog sections.

### Automated tests

- Catalog unit tests with valid and invalid fixtures.
- Artifact file-selection tests, including legitimate PDF assets.
- Shared dependency closure tests.
- Asset-mode and fallback tests.
- Safe output-directory behavior tests.
- Deterministic archive tests.
- Source-versus-artifact isolation tests.
- Compiler command construction tests.
- Shell helper tests using a local fixture server or mocked download.
- Minimal LaTeX fixtures for article/report/book/Beamer consumers of shared
  modules.

Tests must use temporary directories and must not modify template source.

## 12. Current-template migration

### PoliTo Beamer

1. Preserve the current work before structural changes.
2. Complete license and upstream attribution review.
3. Separate the minimal starter from the large demonstration.
4. Move user metadata into `config.tex` or a compact clearly marked preamble.
5. Rename local implementation files where useful while retaining upstream
   attribution and license notices.
6. Remove starter-only dependencies that exist solely for the showcase.
7. Declare every PNG/PDF/background asset and its policy.
8. Verify compilation with and without non-redistributable assets.
9. Generate the preview from `showcase.tex` in the packed artifact.
10. Publish initially as `beta`, promoting to `stable` only after Gate L, Gate A,
    documentation, and compatibility tests pass.

### Other existing entries

- Mark the five placeholder templates `draft` immediately.
- Do not present them in the README as available downloads.
- Preserve their intended IDs unless the taxonomy is clearly wrong.
- Implement and promote them one at a time.
- Prefer one high-quality generic template before adding multiple branded
  variants.

### Recommended implementation order

1. PoliTo Beamer beta.
2. Generic academic Beamer or report template.
3. PoliTo MSc thesis, after current official requirements are verified.
4. UniFi BSc thesis, after current official requirements are verified.
5. Course-project combined report/slides.
6. First Typst template.

## 13. CI design

Replace the current workflows with explicit validation, build, and publication
stages.

### Pull request / push workflow

1. `catalog`: schema and repository validation.
2. `python-tests`: internal tooling tests.
3. `discover`: emit matrices from validated catalog data.
4. `source-compile`: compile beta/stable source entry points.
5. `pack`: build artifacts in release-equivalent mode.
6. `artifact-compile`: compile all packed entry points in isolation.
7. `preview`: render PDFs/thumbnails from packed artifacts.
8. `report`: publish a human-readable matrix summary and upload debug artifacts
   only when useful.

### Release workflow

1. Trigger from a signed or protected `v*` tag.
2. Verify the tag matches `release_version` and the changelog.
3. Run the entire validation and artifact pipeline without `|| true`.
4. Build only beta/stable public artifacts; optionally mark beta clearly.
5. Generate ZIPs, previews, checksums, catalog snapshot, and release index.
6. Create the GitHub Release only if every required job passes.
7. Upload all assets using names derived from template IDs.
8. Generate release notes including added, changed, promoted, deprecated, and
   removed templates.
9. Run a post-release link check against every generated URL.

### CI rules

- No required compile or preview failure may be suppressed.
- Drafts receive catalog/path validation but need not compile until their first
  usable skeleton exists.
- Actions and toolchain versions are pinned deliberately and updated through
  reviewed maintenance changes.
- CI must not rely on ignored local assets or secrets for public artifacts.

### Gate C

- The same artifact tested in CI is the artifact uploaded to the release.
- All generated links exist.
- Failed previews or companion documents block publication.
- The workflow summary makes each template/entry-point result visible.

## 14. Documentation and user experience

### Root README

The README should answer, in order:

1. What Apograph is.
2. Which templates are actually usable now.
3. How to download or open one online.
4. How to compile it locally.
5. How to contribute or report a problem.

Generate the available-template table from the catalog. Show beta/stable status,
preview, direct download, and online-open buttons. Do not list drafts as
available.

### Per-template README

Each beta/stable artifact includes:

- preview;
- intended use and institution relationship;
- compiler and compatibility;
- minimal start instructions;
- supported customization points;
- required/optional assets;
- local, VS Code, and Overleaf instructions where applicable;
- provenance, license, and disclaimer;
- known limitations;
- template and Apograph release provenance.

### Maintainer documentation

- `architecture.md`: source-to-artifact data flow and boundaries.
- `authoring.md`: how to add a template and satisfy gates.
- `asset-policy.md`: asset modes and branding rules.
- `catalog-reference.md`: schema field definitions and examples.
- `licensing.md`: mixed-license structure and attribution checklist.
- `release-process.md`: release candidate, tag, validation, publication, and
  rollback procedure.
- `CONTRIBUTING.md`: contribution workflow and review expectations.
- `AGENTS.md`: repository commands, invariants, generated-file rules, and
  verification steps for Codex or other coding agents.

## 15. Editor and online integrations

### VS Code

Include a minimal generated `.vscode/` adapter in relevant artifacts:

- recommended LaTeX Workshop or Tinymist extension;
- output directory and compiler recipe;
- no absolute paths;
- no dependence on monorepo `TEXINPUTS`;
- no strong personal preferences such as forced auto-save, theme, or formatting.

The repository-level configuration may remain more opinionated for maintainers.

### Overleaf

- ZIP root contains the starter and no wrapper directory.
- Compiler requirements are documented and, where possible, encoded in project
  files compatible with Overleaf.
- Website and README generate an encoded
  `https://www.overleaf.com/docs?snip_uri=<release-zip>` link.
- Manual ZIP upload remains documented as the fallback.
- Do not make premium Git/GitHub synchronization part of the basic promise.

### Other editors

Keep artifacts editor-neutral. Document the ordinary compiler command so users
of TeXstudio, Neovim, Emacs, or terminal workflows are not second-class.

## 16. Shell helper

Keep `scripts/use.sh` as an optional convenience, not the canonical interface.

### Redesign

```bash
apograph-use <template-id> [--version VERSION] [--out DIRECTORY]
```

- Accept the exact catalog ID rather than reconstructing it from three positional
  facets.
- Download only canonical GitHub Release assets.
- Verify the release checksum.
- Extract into a new or empty destination.
- Refuse destructive overwrite by default.
- Do not download or execute a second Python asset implementation.
- Do not require Python.
- Print local and Overleaf next steps from artifact metadata where feasible.

A PowerShell equivalent is optional and should be added only if Windows users
request a terminal installer. Direct ZIP downloads remain cross-platform.

## 17. Static website

Build the first website only after the release URLs and catalog schema are
stable. Host it initially as the repository's GitHub Pages site, independent of
the personal homepage.

### MVP

- generated from `CATALOG.json`;
- cards for beta/stable templates only;
- preview thumbnail and full PDF;
- filters for purpose, institution, format, and status;
- template detail pages;
- direct latest and pinned download links;
- Open in Overleaf for LaTeX;
- native Typst action when available;
- responsive and keyboard-accessible UI;
- clear unofficial/endorsed/official status and license link.

### Build and deployment

- Prefer a small static generator using the internal catalog module.
- Avoid a database, server, authentication, or client framework unless a real
  requirement appears.
- Generate into a CI artifact or dedicated Pages output, not hand-edited HTML.
- Fail the Pages build on catalog or broken-link errors.
- Keep URLs stable by template ID.

### Gate W

- Every displayed template has a valid preview and download.
- One-click online actions use the exact tested release artifact.
- The site contains no independently maintained metadata.

## 18. Typst pilot

Introduce Typst only after the cross-format catalog and artifact contracts are
working for LaTeX.

### Tasks

1. Add `shared/typst/` only for genuinely reusable source modules.
2. Build one real generic Typst template rather than placeholder parity for all
   LaTeX variants.
3. Use a template function with clear named arguments and a minimal `main.typ`.
4. Add Typst compilation, artifact isolation, and previews to CI.
5. Add `typst.toml` and Universe-compatible structure when mature.
6. Publish to Typst Universe after license, documentation, and quality review.
7. Link the Apograph page to `typst init` and the Typst web-app action.

Do not force LaTeX and Typst to have identical internal file structures; require
only the same catalog, artifact, documentation, and quality concepts.

## 19. Future CLI decision gate

Do not schedule CLI implementation merely because Python tooling exists.
Re-evaluate when at least two of these are true:

- users repeatedly ask for interactive discovery;
- Windows terminal initialization is materially inconvenient;
- there are enough public templates that README/website filtering is insufficient;
- provenance or update checks provide clear value;
- environment diagnostics would solve recurring support issues;
- non-GitHub registries or mirrors need one client interface.

### Initial CLI scope if approved

```text
apograph list
apograph info <id>
apograph init <id> [directory] [--version]
apograph doctor [directory]
```

- Package as an application for `pipx`/`uv tool`, not as an advertised Python
  programming API.
- Read a versioned remote catalog and download canonical release assets.
- Verify checksums and write provenance.
- Do not compile documents, duplicate templates, or implement automatic update
  in the first release.
- Add `check-update` only as an informational command before considering
  mutation.

## 20. Community expansion

Add community templates only after the authoring guide, schema, tests, and
license gate are working.

### Required contribution data

- maintainer or responsible owner;
- institution relationship and evidence for any endorsement claim;
- source/upstream history;
- license and asset policy;
- starter and showcase;
- supported compiler versions;
- preview;
- artifact-isolation tests;
- documented customization and limitations.

Templates without an active maintainer may be deprecated. Institution-specific
requirements should record a last-verified date and source URL; staleness should
be visible rather than silently implying compliance.

## 21. Delivery sequence

Implementation should be split into reviewable branches/PRs. Do not combine the
entire plan into one change.

### Phase 0 — preserve and baseline

**Execution:** completed with checkpoint exception on 2026-07-12; see
`docs/WORKTREE_INVENTORY.md`.

**Objective:** protect the current work and establish reproducible observations.

Tasks:

- Review the existing dirty worktree and classify each change as intended source,
  generated output, local asset, or temporary ingestion material.
- Create a checkpoint commit or explicitly documented WIP branch before moving
  paths.
- Capture current successful PoliTo compile and pack commands.
- Record current failures for placeholders and release workflow.
- Add this implementation plan and initial `AGENTS.md` invariants.

Exit criteria:

- No current user work can be lost during migration.
- The baseline is reproducible from a named commit/branch.

### Phase 1 — governance and catalog foundation

**Execution:** completed on 2026-07-12.

**Objective:** make publication eligibility machine-readable.

Tasks:

- Add schema and validation command.
- Migrate catalog fields and statuses.
- Mark placeholder templates draft.
- Remove source `template.json` duplication.
- Add versioning, institution relationship, provenance, and asset-mode contracts.
- Add licensing/asset documentation skeletons and inventory.
- Generate the README template list from the catalog.

Exit criteria:

- Catalog validation is deterministic and tested.
- Public documentation shows only beta/stable entries.
- Every existing file has a known template/status/provenance category.

### Phase 2 — artifact and test foundation

**Execution:** completed on 2026-07-12.

**Objective:** make a packed artifact the tested product.

Tasks:

- Refactor common script logic into the internal module.
- Redesign file selection, shared vendoring, asset handling, metadata generation,
  deterministic ZIPs, checksums, and safe output behavior.
- Compile packed entry points in isolation.
- Add unit/integration fixtures and tests.
- Remove path rewriting where root-vendored shared packages make it unnecessary.

Exit criteria:

- Gate A passes for a minimal fixture and then PoliTo Beamer.
- Legitimate PDF assets survive packing.
- Ignored local assets cannot change release contents.

### Phase 3 — shared modules and PoliTo Beamer beta

**Execution:** completed on 2026-07-12.

**Objective:** ship one genuinely usable beta through the new pipeline.

Tasks:

- Split shared primitives from template policy.
- Add class compatibility fixtures.
- Restructure PoliTo starter/showcase/config/theme.
- Complete its license and asset decisions.
- Add artifact README and editor adapter.
- Generate preview from the packed showcase.

Exit criteria:

- Gate L and Gate A pass.
- PoliTo Beamer is marked beta.
- A new user can download, compile, and open it in Overleaf without repository
  knowledge.

### Phase 4 — CI and first release candidate

**Execution:** completed on 2026-07-13.

Runner evidence:

- Run `29210122561` passed catalog discovery and both public source entry points.
- Run `29210672054` passed catalog validation, Python tests, and both source
  entry points. Its packed-artifact job reached and passed all 36 tests, then
  failed because Git rejected the container-mounted checkout as dubious
  ownership. The workflow-level fix scopes `safe.directory` to
  `GITHUB_WORKSPACE`.
- Run `29234325379` confirmed that trust fix and again passed catalog, Python,
  source compilation, and all 36 container tests. Artifact publication then
  failed with `EXDEV` because `/tmp` and the mounted workspace are different
  filesystems. The builder now creates its owned staging transaction under the
  output directory, preserving same-filesystem `os.replace` semantics.
- Run `29235231851` passed all six required Compile Templates jobs, including
  packed artifact creation, candidate upload, and the strict pipeline summary.
- Manual Release run `29235596362` succeeded for
  `847240b6aba98680c099cce93c03c7399b4f9141`. It uploaded `CATALOG.json`, the
  ZIP, ZIP checksum, preview, build report, and release index as one workflow
  artifact. The summary reported `Published: false`; no tag or GitHub Release
  was created.

**Objective:** automate exactly the workflow used locally.

Tasks:

- Replace compile and release workflows.
- Add validation/build/artifact-compile/preview matrices.
- Remove suppressed failures.
- Add checksums, release catalog, link checks, and changelog validation.
- Run an unpublished release-candidate build.

Exit criteria:

- [x] Gate C passes from a clean GitHub Actions checkout.
- [x] The release candidate is byte/file equivalent to the tested output.

### Phase 5 — documentation and v0.1.0 beta release

**Objective:** publish a small honest release, not a large placeholder catalog.

Tasks:

- Finish root and per-template documentation.
- Verify all links and online flows manually once.
- Publish only the PoliTo beta and any other template that independently passes
  all gates.
- Attach previews, checksums, catalog snapshot, and notices.
- Record known limitations and feedback channels.

Exit criteria:

- A public release exists and is reproducible.
- README download and Overleaf actions work.
- Drafts are not misrepresented as available products.

### Phase 6 — second generic template

**Objective:** prove the architecture is reusable rather than tailored to one
Beamer theme.

Tasks:

- Implement one generic academic presentation or report fully.
- Reuse only appropriate shared primitives.
- Exercise non-branded asset and licensing paths.
- Refine authoring documentation from the experience.

Exit criteria:

- Two substantially different templates pass all gates.
- No template-specific special case has leaked into the generic builder.

### Phase 7 — static gallery

**Objective:** improve discovery and no-terminal onboarding.

Tasks:

- Generate the GitHub Pages site from catalog and release metadata.
- Add previews, filters, detail pages, download, and Overleaf actions.
- Add Pages CI and broken-link tests.

Exit criteria:

- Gate W passes.
- The website contains no hand-maintained catalog copy.

### Phase 8 — remaining LaTeX templates

**Objective:** promote draft ideas individually based on real quality.

Tasks:

- Verify current institutional requirements before branded thesis work.
- Implement, test, document, and promote one entry at a time.
- Add deprecation/migration notes if IDs or interfaces change.

Exit criteria:

- Each promotion is independently reviewable and releasable.

### Phase 9 — Typst pilot

**Objective:** validate the cross-format architecture and native distribution.

Tasks and criteria are defined in section 18.

### Phase 10 — CLI reassessment

**Objective:** make a data-driven decision using support feedback and usage.

Do not implement unless the decision gate in section 19 is met.

## 22. Recommended branch/commit structure

Suggested branches:

```text
codex/foundation-catalog
codex/artifact-pipeline
codex/shared-latex-contract
codex/polito-beamer-beta
codex/ci-release-pipeline
codex/docs-first-release
codex/pages-gallery
codex/typst-pilot
```

Keep commits narrow, for example:

```text
docs: define catalog and publication contracts
feat: validate catalog schema and repository paths
refactor: centralize artifact-building primitives
fix: preserve declared PDF assets in release bundles
feat: compile packed artifacts in isolation
refactor: split shared math primitives from theorem policy
feat: separate polito beamer starter and showcase
ci: gate releases on packed artifact compilation
docs: generate template availability table from catalog
```

Each branch must begin from a known checkpoint and end with its own relevant
tests passing. Do not reformat unrelated files or absorb unrelated user changes.

## 23. Definition of done for a stable template

A template is `stable` only when all items below are true:

- Catalog entry validates.
- Starter is minimal and documented.
- Showcase/preview accurately demonstrates supported features.
- Every declared publishable entry point compiles from source.
- The packed artifact compiles in isolation.
- Missing user-provided assets use a compiling fallback.
- Included assets are declared and legally redistributable.
- Upstream provenance, license, notices, and institution relationship are clear.
- Shared dependencies are explicit and vendored.
- No monorepo environment variable or absolute path is required.
- Local editor and plain command-line instructions work.
- Overleaf upload and one-click import work for LaTeX.
- Preview and direct download links resolve.
- Supported compiler/toolchain versions are recorded.
- Artifact metadata records release and source commit.
- Checksums are published.
- CI tests the exact uploaded artifact.
- Known limitations and maintenance owner are documented.

## 24. Execution rules

- Preserve the user's current uncommitted work.
- Start with Phase 0; never begin by moving or deleting current assets.
- Treat license uncertainty as a publication-status issue, not a reason to hide
  provenance or guess.
- Prefer generated data over duplicated metadata.
- Prefer failing release builds over publishing incomplete artifacts.
- Keep drafts cheap and stable templates demanding.
- Add interfaces only after their underlying artifact contract is stable.
- At the end of every phase, update this plan with completed items, deviations,
  decisions, and newly discovered constraints.

## 25. First execution prompt

Use the following scope for the first implementation task:

> Execute Phase 0 and Phase 1 of `docs/IMPLEMENTATION_PLAN.md`. Preserve all
> existing uncommitted work. First inventory and classify the dirty worktree,
> then establish a safe checkpoint. Implement the catalog schema, validation,
> statuses, provenance/asset fields, generated public template listing, and the
> initial governance documentation. Do not yet restructure the PoliTo theme or
> rewrite the artifact pipeline. Verify validation and documentation generation,
> and stop with a reviewable diff and a report of any licensing decisions that
> still require human evidence.

This first slice deliberately avoids combining metadata migration with template
file moves and packer changes.

## 26. Recommended Codex execution workflow

Use Codex in the desktop app as the primary orchestrator for this roadmap, with
VS Code as the inspection and visual-authoring companion.

### Phase 0 exception

Run Phase 0 in the current local checkout because it must inspect and preserve
the existing uncommitted and ignored files. Do not start that inventory in a new
worktree: ignored branding assets and other local-only files may not be present
there.

### After the checkpoint

For each later delivery phase:

1. Start one Codex desktop task from the relevant checkpoint.
2. Use a dedicated `codex/<scope>` worktree or branch.
3. Give the task one phase or one coherent subset of a phase, not the entire
   remaining roadmap.
4. Require implementation, tests, updated plan status, and a reviewable diff.
5. Open that worktree in VS Code when manual LaTeX/Typst editing, PDF inspection,
   or close diff review is useful.
6. Return review findings to the same task for corrections.
7. Commit/merge only after the phase exit criteria pass.
8. Start the next phase from the updated main branch.

### Use the desktop app for

- repository-wide analysis and multi-file migrations;
- long-running build/test loops;
- worktree isolation and phase coordination;
- CI/release workflow work;
- maintaining roadmap context across several tasks;
- comparing and reviewing completed delivery slices.

### Use the VS Code Codex extension for

- focused changes around files already open;
- explaining or revising a selected LaTeX/Typst section;
- inspecting diffs beside their source;
- tight edit/compile/preview iteration;
- follow-up fixes discovered during visual review.

### Concurrency rule

Do not let two Codex tasks edit the same checkout or overlapping files at the
same time. Parallel work is acceptable only in separate worktrees with clearly
separated ownership and integration order. For Apograph, sequential phases are
preferable until the catalog and artifact contracts stabilize.
