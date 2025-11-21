# Architecture

## Overview
- Modular Python package
- CLI entry via `src/main.py`
- Core modules: gene detection, BLAST/DIAMOND wrapper, result interpretation, visualization
- Rich integration for CLI and logging

## Data Flow
1. Input FASTA(s) validated
2. BLAST/DIAMOND/mock search
3. Gene hits mapped to antibiotic classes
4. Results written to CSV and visualized
