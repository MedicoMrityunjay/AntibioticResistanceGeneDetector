# streamlit_app/utils.py
"""
Utility helpers for the Streamlit UI.
- Save uploaded files to a temporary folder
- Validate simple FASTA format by attempting to read with Bio.SeqIO
- Helpers to discover result CSVs and plot files in an output directory
- Read VERSION file safely
"""
from pathlib import Path
from typing import List
import zipfile
import io

try:
    from Bio import SeqIO
except Exception:
    SeqIO = None

import pandas as pd


def save_uploaded_files(uploaded_files, target_dir: Path, allowed_extensions=None) -> List[Path]:
    """Save uploaded `UploadedFile` objects (Streamlit) to `target_dir`.

    Performs basic validation: enforces allowed extensions (if provided), rejects empty files,
    and validates FASTA format using `validate_fasta` when possible.

    Returns list of successfully written file paths.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    allowed_extensions = [e.lower() for e in (allowed_extensions or [])]
    for u in uploaded_files or []:
        name = getattr(u, "name", None) or f"upload_{len(paths)+1}.fasta"
        dest = target_dir / name

        # extension check
        if allowed_extensions:
            if not any(str(dest).lower().endswith(ext) for ext in allowed_extensions):
                continue

        # Streamlit's uploaded file has `getbuffer()` or .read()
        data = None
        try:
            data = u.getvalue()
        except Exception:
            try:
                data = u.read()
            except Exception:
                data = None
        if not data:
            continue
        # write bytes
        try:
            with open(dest, "wb") as fh:
                if isinstance(data, str):
                    data = data.encode("utf-8")
                fh.write(data)
        except Exception:
            continue

        # basic FASTA validation
        try:
            if not validate_fasta(dest):
                # remove invalid file
                try:
                    dest.unlink()
                except Exception:
                    pass
                continue
        except Exception:
            # if validation fails unexpectedly, keep file but do not add
            try:
                dest.unlink()
            except Exception:
                pass
            continue

        paths.append(dest)
    return paths


def validate_fasta(path: Path) -> bool:
    """Quick validation of a FASTA file by attempting to parse one record.

    Returns True if parsed successfully (Bio not required but recommended).
    """
    path = Path(path)
    if not path.exists():
        return False
    if SeqIO is None:
        # Fallback: check basic header char
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            first = fh.readline()
            return first.startswith(">")
    try:
        it = SeqIO.parse(str(path), "fasta")
        next(it)
        return True
    except Exception:
        return False


def find_results_csv(outdir: Path) -> List[Path]:
    outdir = Path(outdir)
    if not outdir.exists():
        return []
    return sorted(outdir.glob("**/*.csv"))


def find_plot_files(outdir: Path) -> List[Path]:
    outdir = Path(outdir)
    if not outdir.exists():
        return []
    exts = ("*.png", "*.svg", "*.pdf", "*.jpg", "*.jpeg")
    files = []
    for e in exts:
        files.extend(sorted(outdir.glob(f"**/{e}")))
    return files


def zip_files_to_bytes(paths: List[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            zf.write(p, arcname=p.name)
    buf.seek(0)
    return buf.read()


def read_version_safe(version_path: Path) -> str:
    version_path = Path(version_path)
    try:
        return version_path.read_text(encoding="utf-8").strip()
    except Exception:
        return "unknown"
