# Licensing and provenance

## Repository license boundary

The root MIT license covers original Apograph tooling and original material for
which the repository has authority to apply it. It does not automatically
relicense imported themes, upstream templates, university marks, or other
third-party assets.

Template and asset records in `CATALOG.json` carry their own license status. A
`review-required` status blocks promotion to beta/stable.

## Current evidence inventory

### Original draft placeholders and tooling

The current generic placeholder files, scripts, catalog tooling, and Apograph
shared source are treated as original MIT work. Institution formatting accuracy
and use of brand identifiers are separate verification questions.

### PoliTo Beamer theme

Phase 3 identified the direct file-level comparison base as Andrea Gasparini's
`sapienza-beamer-template` commit
`24651c2ec532eb88544056c9b8130b7907fb553c`. Comparing that revision to the
preserved PoliTo input accounts for the declared PoliTo adaptation and local
path/content edits. Its GPL-3.0 license and the inherited file header name:

- Federico Zenith;
- Håvard Berland;
- Mattia Ippoliti;
- Andrea Gasparini;
- Liu Qilong;
- local Apograph modifications by Elia Innocenti.

The current theme code retains a GPL-3.0-or-later notice. The adapted showcase
content traces to Mattia Ippoliti's Overleaf template ID 27027, which Overleaf
labels CC BY 4.0. The preserved local reference archive has SHA-256
`bcb64bde2025c9d5b4fde6be9324792768c63e01434641176f59f2720afedf71` and a
2024-11-06 file timestamp; it also contains earlier local path changes, so it is
not represented as an untouched upstream release.

The artifact ships `GPL-3.0-or-later AND CC-BY-4.0` as the proposed component
expression, complete license texts, a modification record, attribution, and a
non-endorsement statement. Maintainer Elia Innocenti reviewed and accepted this
component boundary and the shipped notices on 2026-07-12. The catalog therefore
records the template license as `verified`; the Overleaf project-level CC BY
label and embedded GPL code notice remain distinct components rather than being
collapsed into a guessed single license.

### PoliTo thesis

The `thesis-polito-latex` candidate adapts Luigi De Russis's “Politecnico di Torino
Thesis Template” on Overleaf, whose project page identifies Luigi De Russis and
CC BY 4.0. The source was reviewed as a template for both Bachelor's and
Master's theses using `toptesi` and its own 2023 title page.

Apograph records the adapted thesis/title-page files as CC-BY-4.0 and the
separately vendored shared modules as MIT. Its `NOTICE` identifies the upstream,
the 2026 modifications by Elia Innocenti, published guidance used as design
evidence, and the non-endorsement boundary. Maintainer Elia Innocenti reviewed
and accepted the `CC-BY-4.0 AND MIT` component boundary, shipped notices, and
non-endorsement statement on 2026-07-18, so the catalog records the template
license as `verified`. Neither published guidance nor the upstream project
establishes official endorsement. Both degree modes pass isolated packed-
artifact compilation in TeX Live 2026, and a packed ZIP of the promoted source
revision was successfully compiled on Overleaf with pdfLaTeX on 2026-07-18.

The current fidelity baseline preserves the upstream pdfLaTeX-compatible Latin
Modern typography; it does not substitute Carlito or claim to implement the
Visual Identity Manual's Poppins typography. Optional Poppins support may be
added later as a separate profile with its own font-license record and
LuaLaTeX/XeLaTeX compatibility gates.

### Institution assets

Local PoliTo logos/backgrounds and the expected PoliTo/UniFi logos have no
recorded redistribution evidence. They remain ignored or user-provided. Their
presence on a public site or inside an upstream archive is not sufficient proof
that Apograph may redistribute them.

## Human decisions still required

1. Identify the exact source and copyright owner of each local PNG.
2. Determine whether PoliTo and UniFi permit redistribution of their marks in an
   unofficial open-source template.
3. Decide whether textual institution references require a non-endorsement or
   trademark notice beyond the current relationship field.

## Evidence standard

For publication, keep a durable URL or copied license text, upstream revision,
file mapping, author/owner, and reviewer/date. If evidence remains unclear, keep
the file user-provided or replace it with an original non-branded fallback.

This document tracks engineering release decisions and is not legal advice.
