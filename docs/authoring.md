# Template authoring guide

This is the initial authoring contract. It will be refined after the first two
templates pass the complete artifact pipeline.

## 1. Establish rights and purpose

Before copying source, decide whether the work is original, adapted, or
redistributed. Record upstream URLs, revisions, authors, licenses, institution
relationship, and asset policies.

## 2. Choose an ID and path

Use:

```text
templates/<purpose>/<variant>/<format>/
```

The ID normally combines purpose, variant, and format, for example
`presentation-beamer-polito-latex`. IDs are permanent once published.

## 3. Add a draft catalog entry

Provide every required catalog field. Use `null` and `review-required` for
unknown legal evidence instead of guessing. Do not add a source `template.json`.

## 4. Separate user and implementation surfaces

Aim for:

```text
main.tex or main.typ     minimal starter
config.tex               common user metadata, where useful
content/                 user document content
showcase.*               richer preview/demo, when useful
theme/                   template-specific implementation
theme/assets/            declared template assets
README.md                usage and limitations
NOTICE                   required attribution
```

Do not force LaTeX and Typst into identical internal structures. They share the
same catalog, artifact, documentation, and quality concepts.

## 5. Keep shared code genuinely shared

Place only small composable primitives in `shared/`. Layout, spacing, headers,
captions, chapter style, and Beamer policy normally belong to the template.
`apograph-math` and `apograph-typography` are deliberately class-neutral;
optional theorem numbering lives in the separate, namespaced
`apograph-theorems` module.

## 6. Validate continuously

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py generate-readme --check
python3 -m unittest discover -s tests -v
python3 scripts/pack.py <template-id>
```

The pack command compiles every artifact-included entry point without
monorepo-only search paths. `--skip-compile` is a developer diagnostic only and
is rejected in release mode.

## 7. Promote through review

Draft status allows incomplete implementation. Beta/stable status is a reviewed
statement about usability and evidence. Use the complete definition of done in
`docs/IMPLEMENTATION_PLAN.md`; do not promote solely because one local compile
succeeds.
