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

## Start in VS Code

Open the extracted project folder and install the recommended LaTeX Workshop
extension when prompted. The release artifact includes `.vscode/settings.json`
with a `latexmk (pdflatex)` recipe that writes generated files under `out/`.
Open `main.tex` and run **LaTeX Workshop: Build LaTeX project**.

`showcase.tex` is a feature tour used to generate the preview. Its supporting
slides live under `showcase/`, are not loaded by `main.tex`, and can be removed
together with `showcase.tex` when you no longer need the component guide. The
showcase intentionally loads more packages than the minimal starter.

## Start in Overleaf

Upload the complete Apograph release ZIP as a new project and select `main.tex`
as the main document. The artifact already contains every source dependency at
project root. No `TEXINPUTS`, repository checkout, or asset download is needed.

The packed starter and showcase were verified with Overleaf pdfLaTeX and TeX
Live 2025 on 2026-07-12, without optional institution assets.

## Compatibility and limitations

- Tested with pdfLaTeX in TeX Live 2025 (Overleaf) and TeX Live 2026 (CI).
- The theme is unofficial and does not claim compliance with a current PoliTo
  presentation standard.
- Institution branding is intentionally absent from the distributed ZIP; the
  compiling fallbacks are the default legal-safe experience.
- The release is beta: public commands and layout details may still change
  before a stable release.

## Project structure

```text
main.tex                         minimal starter entry point
config.tex                       title metadata and common customization
content/slides.tex               starter presentation content
showcase.tex                     richer preview and component guide
showcase/slides/                 showcase-only demonstration slides
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

Release artifacts also contain generated `template.json` and `APOGRAPH.md`
files recording the collection version, exact source commit, dependency list,
asset policy, and checksums. Report reproducible problems through
[Apograph Issues](https://github.com/eliainnocenti/apograph/issues) and include
the template ID, collection version, compiler, and the smallest failing source.
