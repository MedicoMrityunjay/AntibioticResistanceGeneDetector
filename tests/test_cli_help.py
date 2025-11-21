import subprocess
import sys
import os

def test_help_contains_flags():
    repo = os.path.abspath(os.path.dirname(__file__) + os.sep + '..')
    script = os.path.join(repo, 'src', 'main.py')
    res = subprocess.run([sys.executable, script, '-h'], capture_output=True, text=True)
    assert res.returncode == 0
    out = res.stdout
    # check a few key flags present with their short descriptions
    assert '--input' in out
    assert 'Input FASTA file or directory' in out
    assert '--db' in out
    assert 'Resistance gene DB FASTA' in out
    assert '--plot' in out
    assert 'Save heatmap' or 'plots' in out
