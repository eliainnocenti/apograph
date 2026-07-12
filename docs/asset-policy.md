# Asset and branding policy

An asset is any non-source dependency such as a logo, background, font, image,
or generated visual required or demonstrated by a template.

## Modes

### `bundled`

The file is committed and may legally be redistributed in Apograph artifacts.
The catalog records its source, checksum where appropriate, and license status.

### `fetched`

The build downloads the file from a stable authorized URL and verifies its
SHA-256 checksum. Public availability by itself is not evidence of redistribution
permission. A fetched asset still needs license and trademark evidence.

### `user-provided`

The file is not redistributed. The artifact documents the expected path and,
when optional, includes a compiling fallback. Institution logos default to this
mode until redistribution rights are established.

### `generated`

The build produces the asset from repository-owned inputs. Inputs, generation
command, and output checksum are reproducible.

### `placeholder`

No external file is needed; the template intentionally renders a fallback or
ships an instructional marker.

## Rules

- Every asset is declared in `CATALOG.json`.
- Ignored local assets never become release inputs implicitly.
- `fetched` assets require an HTTPS source and pinned checksum.
- Optional `user-provided` assets require a fallback.
- Stable templates compile without absent user-provided assets.
- File extensions are not blanket inclusion/exclusion rules; legitimate PDF
  assets must survive packing.
- Source, license, attribution, and trademark status are separate facts.
- `official` is an institution relationship, not an asset filename or visual
  similarity claim.

## Current institution assets

The local PoliTo PNG files are ignored and classified as user-provided pending
evidence. Their preservation hashes are recorded in
`docs/WORKTREE_INVENTORY.md`. The PoliTo and UniFi PDF logo placeholders likewise
represent unresolved user-provided assets, not downloadable dependencies.

## Human evidence checklist

Before changing an asset to `bundled` or `fetched`, record:

1. the authoritative source;
2. the exact file/revision;
3. copyright owner;
4. redistribution terms;
5. modification terms;
6. required attribution;
7. trademark/brand restrictions;
8. whether the template may imply endorsement;
9. checksum;
10. fallback if the source later disappears.
