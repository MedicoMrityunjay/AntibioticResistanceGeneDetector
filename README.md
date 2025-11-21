AntibioticResistanceGeneDetector

High-performance antibiotic resistance gene detection with BLAST+/DIAMOND, rich reporting, Streamlit UI, background job system, and 3D visualization.

Overview

AntibioticResistanceGeneDetector is a full-stack, production-grade toolkit for detecting antibiotic resistance genes in FASTA files.
It includes:

CLI detection pipeline using BLAST+ or DIAMOND

Automatic database indexing

Rich terminal UI with progress bars and styled tables

Batch processing engine

Visualization (heatmap, bar chart, network)

Robust error handling + safe-fail outputs

Streamlit Web UI with:

Uploads

Real-time progress

Background jobs

Worker heartbeat + logs

Persistent background worker

A standalone 3D web visualization site (site3d)

Complete CI/CD pipeline supporting PyPI + TestPyPI

Built for research, pipelines, CLI users, and web interfaces.

Features
Core Pipeline

FASTA validation (single or folder)

Automatic selection of DIAMOND → BLAST+ → mock mode

Rich terminal output (color tables, logs)

Batch processing with multi-threading

Generates CSVs, logs, and plots

Visualizations

Gene-class heatmap

Antibiotic-class bar plot

Gene relationship network

Web UI (Streamlit)

Responsive interface

Progress bars

Background job system

Worker logs + heartbeat

Mock mode (simulation)

Background Worker

Persistent job queue

PID + heartbeat file

Log rotation

Automatic retries

3D Visualization Site

Three.js SPA

Interactive DNA helix

Module hotspots

Animated scenes

Installation
Install From PyPI (recommended)
pip install arg-res-detector

Install From TestPyPI (release candidates)
pip install --index-url https://test.pypi.org/simple/ --no-deps arg-res-detector

Install Locally (development mode)
git clone https://github.com/MedicoMrityunjay/AntibioticResistanceGeneDetector
cd AntibioticResistanceGeneDetector
pip install -e .

Python Dependencies
pip install -r requirements.txt

BLAST+ & DIAMOND Setup
Windows

Download from official sites, extract, and add bin/ to PATH.

Linux
sudo apt-get install ncbi-blast+
sudo apt-get install diamond-aligner

macOS
brew install blast
brew install diamond

Usage (CLI)
Single FASTA
python AntibioticResistanceGeneDetector/src/main.py \
  --input AntibioticResistanceGeneDetector/input/example.fasta \
  --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
  --map AntibioticResistanceGeneDetector/data/gene_class_map.csv

Batch Folder
python src/main.py \
  --input AntibioticResistanceGeneDetector/input \
  --db AntibioticResistanceGeneDetector/data/resistance_genes.fasta \
  --map AntibioticResistanceGeneDetector/data/gene_class_map.csv \
  --threads 4 --plot

Summary Only
python src/main.py --input input/example.fasta --summary

Quiet Mode
python src/main.py --input input/example.fasta --quiet

Disable Rich Output
python src/main.py --no-rich

Streamlit Web App
Run the UI
streamlit run streamlit_app/app.py --server.port 8501

Features

Upload FASTA files

Folder input

Job queue

Real-time job progress

Mock mode

Worker heartbeat

Log viewer

Auto-refresh

Background Worker System
Start Worker Manually
python streamlit_app/run_worker_entry.py

Start Supervisor (auto-restart)
python streamlit_app/supervise.py

Worker components:

worker.pid

worker.heartbeat.json

Rotating logs in temp/logs/

Atomic job writes

Progress history

3D Visualization Site (site3d)

Run locally:

cd site3d
python -m http.server 8000


Open in browser:

http://localhost:8000


Includes an interactive DNA helix, module hotspots, and animated 3D views.

Project Structure
AntibioticResistanceGeneDetector/
│
├── src/                   # Core detection engine
├── data/                  # Resistance gene DB + mappings
├── input/                 # Sample FASTA
├── output/                # Example output
├── docs/                  # MkDocs documentation
├── site/                  # Auto-generated MkDocs site
├── site3d/                # Three.js visualization site
├── streamlit_app/         # Web UI + worker system
│     ├── app.py
│     ├── handlers.py
│     ├── job_manager.py
│     ├── job_worker.py
│     ├── supervise.py
│     └── temp/ (jobs, logs, output)
└── tests/                 # Full test suite

Continuous Integration (CI/CD)

GitHub Actions include:

docs.yml – builds documentation

tests.yml – runs full test suite

pre_release_validation.yml – validates packaging & versioning

publish_testpypi.yml – publishes RC tags

publish_pypi.yml – publishes stable releases

release.yml – release pipeline

Release tagging rules

Pre-release: v0.1.1-rc1 → TestPyPI

Release: v0.1.1 → PyPI

Troubleshooting
BLAST/DIAMOND not found

System switches to mock mode and logs a warning.

Corrupted FASTA

Skipped with error message and blank output rows.

Permission errors

Run terminal as Administrator or change output directory.

No results

Output still includes summary file; logs explain why.

Roadmap

Support for more databases (CARD, MEGARes v3+)

Web-based interactive plots

Dashboard for job analytics

REST API

Container image (Docker)

Cloud batch execution

Contributing

Pull requests are welcome.

Please follow:

Feature branches: feature/...

Tests required before PR merge

Run formatting: ruff or black

Update CHANGELOG.md for visible changes

License

MIT License.

Citation

If you use this tool in research:

AntibioticResistanceGeneDetector (2025). 
GitHub: https://github.com/MedicoMrityunjay/AntibioticResistanceGeneDetector
