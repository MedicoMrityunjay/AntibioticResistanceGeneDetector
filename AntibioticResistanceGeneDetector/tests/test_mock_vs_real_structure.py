import pytest
from src.run_blast import mock_search, parse_blast_results
from Bio import SeqIO

def test_mock_and_parse_structure(tmp_path):
    # create a fake db fasta
    db = tmp_path / "db.fasta"
    db.write_text(">geneA\nATGCATGCATGC\n>geneB\nATGCATGC\n")
    # mock results
    mock_results = mock_search(str(tmp_path / 'query.fasta'), str(db))
    # create a fake tsv matching parse format
    tsv = tmp_path / "out.tsv"
    with open(tsv, 'w') as f:
        f.write('q1\tgeneA\t99.0\t12\t1\t12\t1\t12\n')
    parsed = parse_blast_results(str(tsv), identity=0, coverage=0)
    # ensure same keys exist
    assert all(isinstance(r, dict) for r in mock_results)
    assert all('gene' in r and 'identity' in r and 'length' in r for r in parsed)
