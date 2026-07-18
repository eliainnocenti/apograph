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

`showcase.tex` is a self-contained teaching deck adapted from Mattia Ippoliti's
original template and is used to generate the preview. It is not loaded by
`main.tex`; remove that single file when you no longer need the reference.

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
showcase.tex                     self-contained teaching deck and preview
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

No asset is required: the distributed project deliberately compiles with text,
plain-background, and neutral-image fallbacks. To reproduce the visual result
of Mattia Ippoliti's original project, provide these five files at the exact
paths and with the exact capitalization shown:

- `theme/assets/logo_RGB.png` — color logo;
- `theme/assets/Logo_RGB_negative.png` — negative logo;
- `theme/assets/background.png` — title background;
- `theme/assets/background_alternative.png` — side-picture background;
- `theme/assets/background_negative.png` — chapter-divider background.

Without them, the logo becomes a small text box and backgrounds become plain or
neutral placeholders. Uncomment `\apographTitleBackground*` in `config.tex` to
enable the split title background in your own presentation.

### Where to obtain authorized files

- PoliTo's student thesis guidance says the title-page template and logo are
  available in the Teaching Portal under **My academic progress → Shared
  drives**, and that students may use the logo for academic purposes. Download
  it there, export or rename it to the exact filename above, and keep your use
  within the permission given to you.
- Mattia Ippoliti's [original Overleaf
  project](https://www.overleaf.com/latex/templates/politecnico-di-torino-presentation/cnypkdbdyqky)
  is the reference for the five filenames and original visual layout. Its
  downloadable project may help an authorized user reconstruct that layout,
  but its public availability is not evidence that PoliTo marks may be reused
  or redistributed in every context.
- PoliTo's [corporate-image
  page](https://www.polito.it/en/polito/about-us/corporate-image) contains the
  current Visual Identity Manual and explains that third-party logo use needs
  authorization. Use its request process when your planned use is not already
  covered by your institutional role or academic permission.

Do not commit these files back to Apograph or include them in a redistributed
ZIP unless you have independently established the necessary copyright and
trademark rights. The Apograph licenses cover the code and adapted teaching
content, not institution marks.

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
