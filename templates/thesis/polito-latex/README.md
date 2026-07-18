# Unofficial PoliTo thesis

This is one configurable LaTeX starter for Bachelor's and Master's theses at
Politecnico di Torino. It adapts Luigi De Russis's
[Politecnico di Torino Thesis
Template](https://www.overleaf.com/latex/templates/politecnico-di-torino-thesis-template/cmpmxftwvvbr),
uses the maintained `toptesi` class, and follows the information requirements
in published PoliTo thesis guidance. It is unofficial and is not endorsed by
Politecnico di Torino.

The default project deliberately reproduces the upstream template rather than
redesigning it: the Latin Modern typography, title-page proportions, document
flow, package feature set, acknowledgements, lists, and introductory teaching
content are preserved. Apograph mainly reorganizes those parts behind a small
configuration surface and a self-contained ZIP.

## Start

1. Edit `config.tex`.
2. Leave `\apographBachelorThesisfalse` for a Master's thesis or change it to
   `\apographBachelorThesistrue` for a Bachelor's thesis.
3. Edit the `\apographPerson{...}` entries for candidates and supervisors.
4. Replace the example files under `content/` with your thesis text.
5. Compile with:

```bash
latexmk -pdf main.tex
```

The starter uses `biber` for references; `latexmk` runs it when required. In
VS Code, use LaTeX Workshop. In Overleaf, upload the complete Apograph artifact
ZIP and select `main.tex` as the main document.

Both degree modes and the no-logo fallback are tested from the isolated packed
artifact with pdfLaTeX in TeX Live 2026. The revised, fidelity-focused ZIP must
still be uploaded to Overleaf before Overleaf compatibility is claimed.

## Configuration surface

`config.tex` contains project metadata and front-matter switches:

- degree level and document language;
- title and optional subtitle;
- degree programme, academic year, and graduation session;
- candidates, supervisors, and optional co-supervisors;
- optional abstract, summary, acknowledgements, list of figures, and glossary.

Each person is one `\apographPerson{...}` entry. Add or remove entries without
editing the title-page implementation. For example:

```latex
\newcommand{\apographSupervisors}{%
  \apographPerson{First Supervisor}%
  \apographPerson{Second Supervisor}%
}
\newcommand{\apographCosupervisors}{%
  \apographPerson{Co-supervisor}%
}
```

Leave `\apographCosupervisors` empty to omit that block completely. The degree
switch selects the corresponding `toptesi` module before the document class
loads.

## Optional PoliTo logo

The project compiles without a logo and renders a same-footprint text fallback.
To reproduce the upstream title page, obtain the horizontal blue 2021 PoliTo
logo used by the original template (the reference file is named
`polito_logo_2021_blu-2-2.jpg`) and place a copy at exactly:

```text
theme/assets/polito-logo.jpg
```

PoliTo's student thesis guidance says the title-page template and logo are
available in the Teaching Portal under **My academic progress → Shared drives**
and that students may use the logo for academic purposes. Download it from that
authenticated area, rename the copy to `polito-logo.jpg`, and keep the path
above unchanged. Obtain the file there rather than from Apograph. PoliTo's
[corporate-image
page](https://www.polito.it/en/polito/about-us/corporate-image) explains the
separate authorization process for third-party use. Do not redistribute the
logo merely because you can access it. The placeholder file in `theme/assets/`
is only an instruction marker; it is not an image.

## Alignment and limitations

The published guidance requires enough information to identify the university,
degree programme, academic year, title, author, supervisor, and any
co-supervisors. This starter exposes all of those fields. Its current visual
baseline follows the upstream template, including its pdfLaTeX-compatible Latin
Modern typography. Optional Poppins support may be explored later as a separate
font/compiler profile; it is not silently substituted into this faithful
baseline.

PoliTo states that there are no general mandatory thesis-writing style rules
and recommends discussing the format with the supervisor. Degree programmes or
supervisors can impose additional expectations, so “aligned” does not mean
official, mandatory, or guaranteed compliant for every programme.

## Structure

```text
main.tex                           compact document assembly
config.tex                         metadata and front-matter switches
bibliography.bib                   bibliography database
glossaries.tex                     optional glossary entries
content/abstract.tex               optional abstract
content/summary.tex                optional summary
content/acknowledgements.tex       acknowledgements
content/chapters/                  thesis chapters
content/appendix.tex               optional appendix example
theme/apograph-polito-thesis.sty   packaged upstream configuration and title page
theme/assets/                      optional user-provided logo
NOTICE                             provenance and modification record
LICENSES/                          component license text
```

## Licensing and provenance

The adapted thesis starter is CC BY 4.0; Apograph shared modules copied into a
release artifact remain MIT. See `NOTICE` for authorship, modifications,
source links, asset exclusions, and non-endorsement. Neither license grants
permission to use institution marks.
