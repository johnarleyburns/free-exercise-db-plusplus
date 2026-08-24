#!/usr/bin/env python3
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("--schema", type=Path, required=True)
args = parser.parse_args()

root = Path(__file__).resolve().parent
env = os.environ.copy()
env["SOURCE_DATE_EPOCH"] = "0"

def build(output: Path) -> str:
    subprocess.run(
        [
            sys.executable,
            str(root / "convert_fedb_to_fedbpp.py"),
            str(args.input),
            str(output),
            "--schema",
            str(args.schema),
            "--completeness",
            "full",
        ],
        check=True,
        env=env,
    )
    return hashlib.sha256(output.read_bytes()).hexdigest()

with tempfile.TemporaryDirectory() as tmp:
    first = Path(tmp) / "first.json"
    second = Path(tmp) / "second.json"

    first_hash = build(first)
    second_hash = build(second)

    assert first_hash == second_hash, (first_hash, second_hash)
    assert first.read_bytes() == second.read_bytes()

    print("reproducible build SHA-256:", first_hash)
