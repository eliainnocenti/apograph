# Artifact contract

The canonical Apograph product is the ZIP produced by `scripts/pack.py`, not a
template directory inside the monorepo.

## Outputs

For template ID `<id>`, one successful build emits:

- `<id>.zip`: deterministic, self-contained project source;
- `<id>.zip.sha256`: checksum sidecar for that ZIP;
- `<id>.build.json`: machine-readable selection, dependency, asset, compile,
  ZIP-checksum, and preview-checksum report;
- `<id>.preview.pdf`: generated from the packed preview entry point when one is
  declared.

The ZIP contains a catalog-derived `template.json`, generated usage guidance,
an optional VS Code adapter, and each declared shared LaTeX package at ZIP root.
The ZIP checksum is external because an archive cannot contain its own final
checksum without making the value self-referential.

An unpublished or tagged collection candidate additionally contains:

- `CATALOG.json`: the exact catalog snapshot used for the build;
- `release-index.json`: the release version, source commit, normalized source
  epoch, catalog checksum, and per-template ZIP/preview/report mapping.

`scripts/release.py assemble` refuses to create that index unless every public
template has exactly one release-mode report and all recorded checksums,
versions, commits, statuses, and source epochs agree. CI uploads this exact
verified directory; a tag publication does not rebuild or select files again.

## File selection

The builder excludes named generated directories, LaTeX auxiliary suffixes,
generated previews/manifests, and entry points marked
`include_in_artifact: false`. It does not exclude broad source formats: a
legitimate PDF remains in the artifact unless its path is generated or governed
by an asset declaration.

Files below `theme/assets/` enter the ZIP only when harmless instructional
markers or catalog assets whose mode allows redistribution. Local ignored marks
cannot influence ZIP bytes. Missing shared dependencies, conflicting root
filenames, required assets, or declared entry points fail the build.

## Asset behavior

- `bundled` files must exist and are checksummed.
- `fetched` files require a URL and pinned checksum and are downloaded only with
  explicit `--fetch-assets`.
- `user-provided` files are always excluded and have exact-path instructions.
- `placeholder` assets require no external file.
- `generated` assets fail until a catalog-backed generator exists.

Current PoliTo/UniFi marks are user-provided. Their fallbacks are part of the
template source, so an artifact must compile without any ignored local image.

## Compilation boundary

Every included starter, showcase, or companion entry point is compiled from the
temporary packed directory. Artifact compilation removes `TEXINPUTS`,
`BIBINPUTS`, and `BSTINPUTS`; source previews may explicitly add the repository
shared directory. `SOURCE_DATE_EPOCH`, `FORCE_SOURCE_DATE`, and UTC are supplied
for reproducible compiler output.

The preview is copied from that packed compilation result. It is never rebuilt
from the source tree during artifact creation.

## Commands and modes

Developer mode permits an exact draft ID:

```bash
python3 scripts/pack.py presentation-beamer-polito-latex
```

Release mode accepts only beta/stable entries, requires a source commit, and
does not allow compilation to be skipped:

```bash
python3 scripts/pack.py --all --mode release --source-commit <sha>
```

Outputs are installed only after the temporary build succeeds. Existing output
files are preserved unless `--force` is explicit. `--keep-failed` retains an
owned temporary directory for diagnostics; it never repurposes or clears a
user-selected directory. Release mode also verifies that the checkout is clean
and that `--source-commit` exactly matches `HEAD`.

## Verification

Run:

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py generate-readme --check
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py scripts/apograph/*.py
```

The artifact tests cover deterministic ZIPs, legitimate PDF preservation,
ignored-asset independence, safe overwrite behavior, root shared dependencies,
clean compiler environments, and an isolated PoliTo Beamer build.
