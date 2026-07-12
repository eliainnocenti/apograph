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
non-endorsement statement. The catalog remains `review-required` until the
maintainer accepts that component boundary; the Overleaf project-level CC BY
label and embedded GPL code notice must not be collapsed into a guessed single
license.

### Institution assets

Local PoliTo logos/backgrounds and the expected PoliTo/UniFi logos have no
recorded redistribution evidence. They remain ignored or user-provided. Their
presence on a public site or inside an upstream archive is not sufficient proof
that Apograph may redistribute them.

## Human decisions still required

1. Review and accept or reject the proposed GPL/CC-BY component boundary for
   the PoliTo artifact.
2. Confirm that the shipped `NOTICE` and complete license texts satisfy the
   applicable attribution and modification-marking duties.
3. Identify the exact source and copyright owner of each local PNG.
4. Determine whether PoliTo and UniFi permit redistribution of their marks in an
   unofficial open-source template.
5. Decide whether textual institution references require a non-endorsement or
   trademark notice beyond the current relationship field.
6. Verify current institutional formatting requirements before describing any
   thesis template as compliant.

## Evidence standard

For publication, keep a durable URL or copied license text, upstream revision,
file mapping, author/owner, and reviewer/date. If evidence remains unclear, keep
the file user-provided or replace it with an original non-branded fallback.

This document tracks engineering release decisions and is not legal advice.
