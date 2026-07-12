# Unofficial PoliTo Beamer presentation

This is an unofficial, self-contained presentation starter. It is not endorsed
by Politecnico di Torino. The default project compiles without institution
logos or backgrounds.

## Start locally

Edit `config.tex`, replace the frames in `content/slides.tex`, then run:

```bash
latexmk -pdf main.tex
```

Build output can be kept outside the source tree with:

```bash
latexmk -pdf -outdir=out main.tex
```

`showcase.tex` is a feature tour used to generate the preview. It intentionally
loads more packages than the minimal starter.

## Start in Overleaf

Upload the complete Apograph release ZIP as a new project and select `main.tex`
as the main document. The artifact already contains every source dependency at
project root. No `TEXINPUTS`, repository checkout, or asset download is needed.

## Project structure

```text
main.tex                         minimal starter entry point
config.tex                       title metadata and common customization
content/slides.tex               starter presentation content
showcase.tex                     richer preview and component guide
sections/                        showcase-only sections
beamerthemeapographpolito.sty    Beamer theme loaded by \usetheme
apograph-polito-colors.sty       theme palette and compatibility aliases
theme/assets/                    optional user-provided branding files
NOTICE                           attribution and modification record
LICENSES/                        component license texts
```

## Theme options

Pass options through `\usetheme`:

```tex
\usetheme[
  sectionpages,          % insert a contents frame at each section
  autoframesubtitles,    % derive frame subtitles from section names
  noslidenumbers         % hide slide numbers
]{apographpolito}
```

All options are disabled by default except slide numbers. The principal public
commands are:

- `\apographCourse{...}`, `\apographStudentID{...}`, and
  `\apographEmail{...}` for title/backmatter metadata;
- `\apographThemeColor{white|main}` for the global color mode;
- `\apographFootlineColor{<color>}` and `\apographFootlineText{...}`;
- `\apographTitleBackground` and its starred split-layout form;
- `\apographBackmatter` and `\apographSetClosingMessage{...}`;
- `apographcolorblock`, `apographchapter`, and `apographsidepic` for optional
  richer layouts.

## Optional institution assets

The following files are never redistributed by Apograph. If you have an
authorized copy under current institution rules, place it at the exact path:

- `theme/assets/logo_RGB.png` — color logo;
- `theme/assets/Logo_RGB_negative.png` — negative logo;
- `theme/assets/background.png` — title background;
- `theme/assets/background_alternative.png` — side-picture background;
- `theme/assets/background_negative.png` — chapter-divider background.

Without them, the logo becomes a small text box and backgrounds become plain or
neutral placeholders. Do not add these files to a redistributed ZIP unless you
have independently established the necessary rights.

## Licensing and provenance

The theme code is GPL-3.0-or-later. Adapted presentation/showcase content is
CC-BY-4.0. See `NOTICE` for exact upstream revisions, authors, modifications,
asset exclusions, and the non-endorsement statement. These licenses do not
grant trademark permission for institution marks.
