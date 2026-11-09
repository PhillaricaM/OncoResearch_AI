"""Build a local adapter linked to the reviewed OncoCompute mean source."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "backend" / "native"


def build():
    compiler = shutil.which("g++")
    if not compiler:
        raise SystemExit("g++ was not found. Install a C++20 compiler and put it on PATH, then retry. See ONCOCOMPUTE.md.")
    output = NATIVE / "bin"
    output.mkdir(exist_ok=True)
    manifest_path = output / "build.json"
    # An interrupted/failed rebuild must never leave a previous build marked ready.
    manifest_path.unlink(missing_ok=True)
    binary = output / ("oncocompute_mean.exe" if os.name == "nt" else "oncocompute_mean")
    flags = ["-std=c++20", "-O2", "-fno-fast-math"]
    if os.name == "nt":
        flags += ["-static"]  # Avoid requiring MSYS2 DLLs in the API process.
    source_paths = ["mean_bridge.cpp", "upstream/src/statistics.cpp", "upstream/include/oncocompute/statistics.hpp", "upstream/SOURCE.json"]
    subprocess.run([compiler, *flags, "-I", str(NATIVE / "upstream/include"), str(NATIVE / source_paths[0]), str(NATIVE / source_paths[1]), "-o", str(binary)], check=True, cwd=output)
    # Real execution also checks that the runtime dependencies are available.
    smoke = subprocess.run([str(binary)], input="3\n1\n2\n3\n", text=True, capture_output=True, check=True, timeout=10)
    if float(smoke.stdout) != 2.0:
        raise SystemExit("Native smoke check failed")
    manifest = {
        "upstream": json.loads((NATIVE / "upstream/SOURCE.json").read_text()),
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
        "flags": flags,
        "sources_sha256": {p: sha256((NATIVE / p).read_bytes()).hexdigest() for p in source_paths},
        "binary_sha256": sha256(binary.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Built and verified OncoCompute mean adapter:", binary)


if __name__ == "__main__":
    build()
