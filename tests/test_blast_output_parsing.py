import pytest
from src.run_blast import parse_blast_results

def test_parse_blast_results_real_and_mock():
    # Simulate BLAST/DIAMOND output
    lines = [
        "query1\tgeneA\t99.5\t100\t1\t100\t1\t100",
        "query2\tgeneB\t85.0\t90\t5\t94\t10\t99"
    ]
    tsv_path = "test_blast.tsv"
    with open(tsv_path, "w") as f:
        for line in lines:
            f.write(line + "\n")
    results = parse_blast_results(tsv_path, identity=90, coverage=80)
    assert len(results) == 1
    assert results[0]["gene"] == "geneA"
    assert results[0]["identity"] == 99.5
    assert results[0]["length"] == 100
    assert results[0]["qstart"] == 1
    assert results[0]["qend"] == 100
    assert results[0]["sstart"] == 1
    assert results[0]["send"] == 100
