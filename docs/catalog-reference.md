# Catalog reference

`CATALOG.json` is validated against `catalog.schema.json` and the repository
semantics implemented by `scripts/catalog.py`.

## Root fields

- `$schema`: relative schema path.
- `schema_version`: version of the catalog contract.
- `release_version`: current collection development/release version.
- `repository`: canonical identity and original-tooling license.
- `templates`: template records.

## Template identity and taxonomy

- `id`: permanent lowercase hyphenated identifier.
- `name`, `description`: human-facing identity.
- `purpose`: thesis, presentation, report, CV, letter, or other.
- `variant`: concise purpose-local variant slug.
- `format`: LaTeX or Typst.
- `status`: draft, beta, stable, or deprecated.

IDs are release filenames and future stable URLs. Never reuse a retired ID for a
different template.

## Institution

- `id`, `name`.
- `relationship`: generic, unofficial, endorsed, or official.
- `requirements_url`: authoritative formatting requirements when applicable.
- `last_verified`: date those requirements were last checked.

`official` requires evidence of endorsement; it cannot be inferred from matching
branding or from a public upstream template.

## Toolchain and entry points

- `compiler`: pdflatex, lualatex, xelatex, or typst.
- `compatibility.texlive`: explicitly tested TeX Live versions.
- `compatibility.overleaf`: untested, compatible, incompatible, or not
  applicable.
- `source_dir`: repository source directory.
- `entrypoints`: path, role, artifact inclusion, and preview selection.

Roles are starter, showcase, companion, and test. Beta/stable templates require
exactly one starter. Stable templates also require a preview entry point.

## Dependencies, provenance, and licensing

- `shared_deps`: explicit repository shared-module paths.
- `license`: expression, verification status, and notes.
- `upstream`: original/adapted/redistributed classification and source evidence.
- `assets`: declared asset policies.
- `maintainers`: responsible people.

An unknown expression is represented by `null` with status `review-required`.
Do not insert a guessed SPDX expression merely to satisfy validation.

## Publication invariants

The validator enforces stronger evidence for beta/stable entries, including a
verified license expression, starter entry point, and an explicit Overleaf result
for LaTeX. Stable entries additionally need preview and tested toolchain data.

## Commands

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py list
python3 scripts/catalog.py list --status draft
python3 scripts/catalog.py generate-readme
python3 scripts/catalog.py generate-readme --check
```
