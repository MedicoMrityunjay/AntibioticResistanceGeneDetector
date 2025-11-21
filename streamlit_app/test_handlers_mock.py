from pathlib import Path
from unittest.mock import patch
import pandas as pd

class DummyUpload:
    def __init__(self, name, content_bytes):
        self.name = name
        self._b = content_bytes
    def getvalue(self):
        return self._b
    def read(self):
        return self._b

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from handlers import run_detection_and_collect

def fake_run_pipeline(args):
    return [
        {"sample": "a.fasta", "gene": "GENE1", "identity": 95.0},
        {"sample": "b.fasta", "gene": "GENE2", "identity": 92.0},
    ]

# Dummy uploads
u1 = DummyUpload("a.fasta", b">s1\nATGC")
u2 = DummyUpload("b.fasta", b">s2\nATGC")

with patch("handlers.run_pipeline", fake_run_pipeline):
    result = run_detection_and_collect(
        uploaded_files=[u1, u2],
        fasta_dir=None,
        db_path="AntibioticResistanceGeneDetector/data/resistance_genes.fasta",
        gene_map="AntibioticResistanceGeneDetector/data/gene_class_map.csv",
        identity=90.0,
        coverage=80,
        threads=1,
        outdir="streamlit_app/temp/mock_out",
        temp_dir=Path("streamlit_app/temp"),
        plot=False,
        summary=True,
        quiet=True,
        rich=False,
        mock_mode=True
    )

print("=== RESULT KEYS ===", result.keys())
print("=== LOGS ===", result.get("logs"))
print("=== DATAFRAME ===")
print(result.get("dataframe"))
print("=== CSV PATHS ===", result.get("csv_paths"))
print("=== PLOT PATHS ===", result.get("plots"))
