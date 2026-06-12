# Apograph

> A curated collection of LaTeX and Typst templates for academic and professional use.

[![Compile Templates](https://github.com/eliainnocenti/apograph/actions/workflows/compile.yml/badge.svg)](https://github.com/eliainnocenti/apograph/actions/workflows/compile.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)


## Available Templates

| Template | Purpose | Institution | Language | ID |
|----------|---------|-------------|----------|----|
| **PoliTo Master's Thesis** | Thesis | Politecnico di Torino | LaTeX | `thesis-polito-msc-latex` |
| **UniFi Bachelor's Thesis** | Thesis | Università di Firenze | LaTeX | `thesis-unifi-bsc-latex` |
| **Academic Beamer Presentation** | Presentation | Generic | LaTeX | `presentation-beamer-academic-latex` |
| **PoliTo Beamer Presentation** | Presentation | Politecnico di Torino | LaTeX | `presentation-beamer-polito-latex` |
| **Academic Report** | Report | Generic | LaTeX | `report-academic-latex` |
| **Course Project Report** | Report | Generic | LaTeX | `report-course-project-latex` |


## Quick Start

### Option 1: Download from GitHub Releases

Download the latest self-contained ZIP from [Releases](https://github.com/eliainnocenti/apograph/releases), unzip, and start writing.

Each ZIP is fully self-contained — all shared dependencies are bundled in. No need to clone the entire repo.

### Option 2: Shell one-liner (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/eliainnocenti/apograph/main/scripts/use.sh \
  | bash -s -- thesis polito-msc latex
```

Arguments: `<purpose> <variant> <language>`

```bash
# More examples:
bash scripts/use.sh presentation beamer-academic latex
bash scripts/use.sh report academic latex --out ./my-report
```

### Option 3: degit (for developers)

Download a specific template directory without cloning the full repo:

```bash
npx degit eliainnocenti/apograph/templates/thesis/polito-msc/latex my-thesis
```

> **Note:** degit copies only the template directory — shared macros are not included. For a self-contained copy, use the Release ZIP or shell one-liner instead.

### Option 4: Clone the entire repo

```bash
git clone https://github.com/eliainnocenti/apograph.git
```


## Using with Overleaf

1. Download the template ZIP from [Releases](https://github.com/eliainnocenti/apograph/releases)
2. Open [Overleaf](https://www.overleaf.com)
3. Click **New Project → Upload Project**
4. Upload the ZIP file

The ZIP is self-contained — it compiles immediately with no additional setup.


## Using with VSCode

The repo includes pre-configured VSCode settings. For the best experience:

1. Open the repo (or a packed template ZIP) in VSCode
2. Install the recommended extensions when prompted:
   - **[LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop)** — compile, preview, intellisense
   - **[Tinymist](https://marketplace.visualstudio.com/items?itemName=myriad-dreamin.tinymist)** — Typst language server
   - **[LTeX](https://marketplace.visualstudio.com/items?itemName=valentjn.vscode-ltex)** — grammar checking
   - **[Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)** — spelling
3. Open any `main.tex` file and save — it compiles automatically

The repo-level settings configure `TEXINPUTS` so that `\usepackage{apograph-math}` resolves correctly from any template.


## Shared Macros Architecture

Templates reference shared packages via `\usepackage{apograph-math}` during development. The `shared/latex/` directory is the **single source of truth** — no copy-paste across templates.

- **In the repo:** `TEXINPUTS` resolves shared packages automatically
- **In release ZIPs:** `pack.py` copies shared deps into the ZIP and rewrites paths
- **In CI:** `TEXINPUTS` is set in the workflow to include `shared/latex/`


## Development

### Prerequisites

- **Python 3.8+** — for scripts
- **MacTeX / TeX Live** — for LaTeX compilation (`pdflatex`, `latexmk`)
- **typst** *(optional)* — for Typst templates

### Common Commands

```bash
make help                                      # show all targets
make list                                      # list available templates
make preview                                   # compile all templates
make preview-one ID=thesis-polito-msc-latex    # compile one template
make pack ID=thesis-polito-msc-latex           # pack one template → ZIP
make pack-all                                  # pack all templates → ZIPs
make pack ID=thesis-polito-msc-latex VSCODE=1  # pack with VSCode config
make fetch-assets                              # fetch institutional assets (logos)
make status-assets                             # check status of assets
make clean-assets                              # remove downloaded assets
make clean-previews                            # remove all template preview PDFs
make clean                                     # remove build artifacts
```


## CATALOG.json

The machine-readable index that powers scripts, CI, and future tooling. Each template entry includes:

| Field | Description |
|-------|-------------|
| `id` | Unique slug: `{purpose}-{variant}-{language}` |
| `name` | Human-readable name |
| `description` | What the template is for |
| `purpose` | `thesis`, `presentation`, or `report` |
| `institution` | Object with `id` and `name` |
| `language` | `latex` or `typst` |
| `compiler` | `pdflatex`, `lualatex`, `xelatex`, or `typst` |
| `version` | Semantic version |
| `source_dir` | Path to the template in the repo |
| `main_file` | Entry point filename |
| `shared_deps` | List of shared packages needed |
| `tags` | Searchable tags |


## License

[MIT](LICENSE) — use these templates however you like.
