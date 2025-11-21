

# AntibioticResistanceGeneDetector

[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://github-copilot.github.io/AntibioticResistanceGeneDetector/)

## Overview

## Development Workflow

**Branch naming:**
- Use `main` for stable development and releases
- Use feature branches for new features (e.g., `feature/rich-integration`)

**Tagging:**
- Release candidates: `vX.Y.Z-rcN` (e.g., `v0.1.2-rc1`) — triggers TestPyPI publish only
- Stable releases: `vX.Y.Z` (e.g., `v0.1.2`) — triggers production PyPI publish

**CI and Publishing:**
- All pushes and PRs run full test and validation workflows
- RC tags run TestPyPI workflow and install validation
- Stable tags run production PyPI workflow, including pre-release validation
- All workflows fail early on any error

**How it works:**
- CI ensures code, packaging, and CLI are always validated before publishing
- TestPyPI is used for pre-release and RC validation
- PyPI is used for stable, production releases

AntibioticResistanceGeneDetector is a robust, production-ready Python tool for detecting antibiotic resistance genes in bacterial genomes. It supports both single-file and batch processing, integrates with BLAST+ and DIAMOND for high-speed similarity search, and provides rich visualizations for gene and antibiotic class detection results.

## Key Features

- **Single-file and batch processing**: Analyze one or many FASTA files with a single command.
- **BLAST+/DIAMOND auto-detection**: Automatically uses DIAMOND (preferred) or BLAST+ if installed, with fallback to mock mode if neither is available.
- **Automated database indexing**: Automatically creates BLAST/DIAMOND databases if missing.
- **Visualization tools**: Generates heatmaps, bar charts, and network plots for batch results.
- **Comprehensive logging**: Timestamped logs for all events and errors.
- **Safe-fail behavior**: Always produces output files, even for failed or corrupted samples.

## Installation

## Installing from PyPI

To install the latest stable release from PyPI:

```sh
pip install arg-res-detector
```

After installation, use the CLI globally:

```sh
arg_res_detector --help
```

To check the installed version:

```sh
arg_res_detector --version
```

## Installing from Release

## Installing from TestPyPI

To install the latest release candidate from TestPyPI:

```sh
pip install --index-url https://test.pypi.org/simple/ --no-deps arg-res-detector
```

After installation, use the CLI globally:

```sh
arg_res_detector --help
```

To check the installed version:

```sh
arg_res_detector --version
```

To install the latest release as a CLI tool:

```sh
pip install .
```

After installation, use the CLI globally:

```sh
arg_res_detector --help
```

This will show all available flags and usage instructions. To check the installed version:

```sh
arg_res_detector --version
```

### Python Dependencies

Install Python 3.8+ and required packages:

```sh
pip install -r requirements.txt
```


### BLAST+ Installation

brew install blast                  # macOS (Homebrew)


#### BLAST+ (Windows)

- Download BLAST+ from [NCBI BLAST Download](https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/)
- Extract and add the BLAST+ `bin` folder to your PATH environment variable.


#### BLAST+ (Linux/macOS)

```sh
sudo apt-get install ncbi-blast+   # Linux (Debian/Ubuntu)
brew install blast                  # macOS (Homebrew)
```

Or download and extract from NCBI as above.


### DIAMOND Installation

brew install diamond                # macOS (Homebrew)


#### DIAMOND (Windows)

- Download DIAMOND from [DIAMOND GitHub Releases](https://github.com/bbuchfink/diamond/releases)
- Extract and add the DIAMOND executable folder to your PATH.


#### DIAMOND (Linux/macOS)

```sh
sudo apt-get install diamond        # Linux (Debian/Ubuntu)
brew install diamond                # macOS (Homebrew)
```

Or download and extract from GitHub as above.

## Preparing Resistance Gene Databases

- Place your resistance gene FASTA (e.g., CARD, MEGARes) in `AntibioticResistanceGeneDetector/data/resistance_genes.fasta`.
- The tool will automatically create BLAST/DIAMOND databases if missing.
- Ensure your gene-to-class mapping CSV is in `data/gene_class_map.csv`.

## Usage Examples

### Single FASTA Input

```sh
python AntibioticResistanceGeneDetector/src/main.py \
   --input AntibioticResistanceGeneDetector/input/example.fasta \
   --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
   --map AntibioticResistanceGeneDetector/data/gene_class_map.csv
```


Rich-enhanced output (default):

```sh
python AntibioticResistanceGeneDetector/src/main.py \
   --input AntibioticResistanceGeneDetector/input/example.fasta \
   --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
   --map AntibioticResistanceGeneDetector/data/gene_class_map.csv
```


Disable Rich output:

```sh
python AntibioticResistanceGeneDetector/src/main.py \
   --input AntibioticResistanceGeneDetector/input/example.fasta \
   --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
   --map AntibioticResistanceGeneDetector/data/gene_class_map.csv \
   --no-rich
```


Examples of Rich tables and progress bars will appear in the terminal when Rich is enabled. If the terminal does not support colors, the tool will fall back to plain text.


### Batch Folder Input

```sh
python AntibioticResistanceGeneDetector/src/main.py \
   --input AntibioticResistanceGeneDetector/input \
   --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
   --map AntibioticResistanceGeneDetector/data/gene_class_map.csv
```


### Additional CLI examples (new flags)

Generate visualizations and use 4 threads, custom output directory:

```sh
python AntibioticResistanceGeneDetector/src/main.py \
   --input AntibioticResistanceGeneDetector/input \
   --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
   --map AntibioticResistanceGeneDetector/data/gene_class_map.csv \
   --outdir results_dir --threads 4 --plot
```

Print summary only (no files written):

```sh
python AntibioticResistanceGeneDetector/src/main.py --input input/example.fasta --summary
```

Run quietly (errors only):

```sh
python AntibioticResistanceGeneDetector/src/main.py --input input/example.fasta --quiet
```


### CLI Flags Reference

Below is a compact reference for all command-line flags supported by `main.py`. Each row shows the flag, a short description, and a one-line usage example.

| Flag | Description | Example |
|---|---|---|
| `--input <path>` | Input FASTA file or directory containing FASTA files to analyze. | `--input input/example.fasta` |
| `--db <path>` | Resistance gene database FASTA used for similarity search (BLAST/DIAMOND). | `--db data/resistance_genes.fasta` |
| `--map <path>` | CSV mapping genes -> antibiotic classes (two columns: gene,class). | `--map data/gene_class_map.csv` |
| `--threads <n>` | Number of worker threads for batch processing (default: 1). | `--threads 4` |
| `--outdir <dir>` | Output directory for CSV, logs, and plots (default: `output/`). | `--outdir results_dir` |
| `--plot` | Generate visualizations (heatmap, bar chart, network) and save to `plots/`. | `--plot` |
| `--summary` | Print a compact summary table to stdout and skip writing full reports. | `--summary` |
| `--quiet` | Quiet mode: only errors are printed; suppress info/progress UI. | `--quiet` |
| `--rich` / `--no-rich` | Enable or disable Rich-enhanced terminal output (colors, tables, progress). Default: enabled. | `--no-rich` |
| `--version` | Print program version (from `VERSION` file) and exit. | `--version` |

Full help example (clean, abbreviated):

```text
usage: main.py [-h] --input INPUT --db DB --map MAP [--threads N] [--outdir DIR]
                      [--plot] [--summary] [--quiet] [--no-rich] [--version]

AntibioticResistanceGeneDetector - detect antibiotic resistance genes in FASTA files.

optional arguments:
   -h, --help            show this help message and exit
   --input INPUT         Input FASTA file or directory
   --db DB               Resistance gene DB FASTA (BLAST/DIAMOND)
   --map MAP             Gene-to-class CSV mapping file
   --threads N           Number of worker threads (default: 1)
   --outdir DIR          Output directory for results and plots
   --plot                Generate and save visualizations
   --summary             Print summary table only
   --quiet               Suppress non-error output
   --rich / --no-rich    Enable/disable Rich terminal output (default: enabled)
   --version             Print version and exit
```



### Visualization Generation (Notebook)

Open `notebooks/demo.ipynb` and run all cells to generate and view:

- Gene detection heatmap
- Antibiotic class bar chart
- Gene-class network plot

sample_id   gene   identity   coverage   antibiotic_class   source_file

## Example Terminal Output

```text
2025-11-21 01:31:20,024 [INFO] Results written to output/results.csv

Summary Table:
sample_id   gene   identity   coverage   antibiotic_class   source_file
example     geneA    100.0      57       Beta-lactam        input/example.fasta
example     geneB    100.0      57       Tetracycline       input/example.fasta
```

sample_id,gene,identity,coverage,antibiotic_class,source_file

## Example CSV Output

```csv
sample_id,gene,identity,coverage,antibiotic_class,source_file
example,geneA,100.0,57,Beta-lactam,input/example.fasta
example,geneB,100.0,57,Tetracycline,input/example.fasta
```


## Mock Mode vs Real Mode

- **Real mode**: Uses DIAMOND or BLAST+ for similarity search if installed.
- **Mock mode**: If neither tool is available, the system simulates detection and logs a warning. Output format remains identical.


## Folder Structure

```text
AntibioticResistanceGeneDetector/
├── data/
│   ├── resistance_genes.fasta
│   └── gene_class_map.csv
├── input/
│   └── example.fasta
├── output/
│   ├── results.csv
│   ├── logs/
│   └── plots/
├── src/
│   ├── main.py
│   ├── run_blast.py
│   ├── gene_detector.py
│   ├── interpret_results.py
│   ├── utils.py
│   ├── error_handling.py
│   └── visualization.py
├── notebooks/
│   └── demo.ipynb
├── tests/
│   ├── test_detector.py
│   ├── test_interpreter.py
│   ├── test_utils.py
│   ├── test_blast_detection.py
│   ├── test_batch_processing.py
│   ├── test_blast_output_parsing.py
│   └── test_report_formatting.py
├── README.md
├── requirements.txt
└── .gitignore
```


## Troubleshooting

- **Missing BLAST/DIAMOND**: Ensure executables are installed and in your PATH. The tool will log a warning and use mock mode if not found.
- **Corrupted FASTA**: Check input files for proper FASTA formatting. Corrupted files are skipped with a warning and empty output.
- **No hits found**: If no resistance genes are detected, output files are still generated and a warning is logged.
- **Permission issues**: Ensure you have write access to the `output/` directory.
- **Database creation errors**: Check that BLAST/DIAMOND executables are available and input FASTA is valid.


## Future Improvements

- Support for additional resistance gene databases
- Advanced filtering and statistics
- Web-based interface
- Interactive visualizations
- Expanded error reporting and diagnostics


## Citation

If you use this tool, please cite:

> AntibioticResistanceGeneDetector, 2025, GitHub Copilot
![PyPI](https://img.shields.io/pypi/v/arg-res-detector?label=PyPI)
![TestPyPI](https://img.shields.io/badge/TestPyPI-pre--release-blue)
![CI](https://github.com/github-copilot/AntibioticResistanceGeneDetector/actions/workflows/publish_pypi.yml/badge.svg)
![License](https://img.shields.io/github/license/github-copilot/AntibioticResistanceGeneDetector)
![Downloads](https://img.shields.io/pypi/dm/arg-res-detector)
