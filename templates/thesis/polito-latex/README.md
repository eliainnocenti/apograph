# Unofficial PoliTo thesis

This is one configurable LaTeX starter for Bachelor's and Master's theses at
Politecnico di Torino. It adapts Luigi De Russis's
[Politecnico di Torino Thesis
Template](https://www.overleaf.com/latex/templates/politecnico-di-torino-thesis-template/cmpmxftwvvbr),
uses the maintained `toptesi` class, and follows the information requirements
in published PoliTo thesis guidance. It is unofficial and is not endorsed by
Politecnico di Torino.

## Start

1. Edit `config.tex`.
2. Leave `\apographBachelorThesisfalse` for a Master's thesis or change it to
   `\apographBachelorThesistrue` for a Bachelor's thesis.
3. Replace `content/abstract.tex` and the files under `content/chapters/`.
4. Compile with:

```bash
latexmk -pdf main.tex
```

The starter uses `biber` for references; `latexmk` runs it when required. In
VS Code, use LaTeX Workshop. In Overleaf, upload the complete Apograph artifact
ZIP and select `main.tex` as the main document.

Both degree modes and the no-logo fallback are tested from the isolated packed
artifact with pdfLaTeX in TeX Live 2026. Overleaf compatibility remains
unclaimed until the exact ZIP has been uploaded and checked there.

## Configuration surface

`config.tex` contains only project metadata:

- degree level and document language;
- title and optional subtitle;
- degree programme, academic year, and graduation session;
- candidates, supervisors, and optional co-supervisors.

Separate multiple people with `\\`. The degree switch selects the corresponding
`toptesi` module before the document class loads and also changes the labels on
the custom title page.

## Optional PoliTo logo

The project compiles without a logo and renders an explicit text fallback. If
you have an authorized copy, place a horizontal PDF logo at exactly:

```text
theme/assets/polito-logo.pdf
```

PoliTo's student thesis guidance says the title-page template and logo are
available in the Teaching Portal under **My academic progress → Shared drives**
and that students may use the logo for academic purposes. Obtain the file there
rather than from Apograph. PoliTo's [corporate-image
page](https://www.polito.it/en/polito/about-us/corporate-image) explains the
separate authorization process for third-party use. Do not redistribute the
logo merely because you can access it.

## Alignment and limitations

The published guidance requires enough information to identify the university,
degree programme, academic year, title, author, supervisor, and any
co-supervisors. This starter exposes all of those fields. The title-page
proportions are adapted from the upstream project and the 2023 Visual Identity
Manual. Carlito is the current portable pdfLaTeX sans-serif fallback; it is not
an exact substitute for the Manual's Poppins typeface. Optional Poppins support
may be added later with a different compiler profile.

PoliTo states that there are no general mandatory thesis-writing style rules
and recommends discussing the format with the supervisor. Degree programmes or
supervisors can impose additional expectations, so “aligned” does not mean
official, mandatory, or guaranteed compliant for every programme.

## Structure

```text
main.tex                          document assembly and packages
config.tex                        user-editable metadata
content/abstract.tex              abstract text
content/chapters/                 thesis chapters
theme/apograph-polito-thesis.sty  title-page implementation
theme/assets/                     optional user-provided logo
NOTICE                            provenance and modification record
LICENSES/                         component license text
```

## Licensing and provenance

The adapted thesis starter is CC BY 4.0; Apograph shared modules copied into a
release artifact remain MIT. See `NOTICE` for authorship, modifications,
source links, asset exclusions, and non-endorsement. Neither license grants
permission to use institution marks.
