import subprocess
import sys
import os

def test_version_flag():
    repo = os.path.abspath(os.path.dirname(__file__) + os.sep + '..')
    script = os.path.join(repo, 'src', 'main.py')
    # run with Python interpreter to get version output
    res = subprocess.run([sys.executable, script, '--version'], capture_output=True, text=True)
    assert res.returncode == 0
    # version should match VERSION file
    with open(os.path.join(repo, 'VERSION')) as vf:
        v = vf.read().strip()
    assert v in res.stdout or v in res.stderr
