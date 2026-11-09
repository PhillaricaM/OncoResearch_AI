"""Run the real compiled OncoCompute implementation; never a Python fallback."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess

NATIVE = Path(__file__).resolve().parent / "native"
BINARY = NATIVE / "bin" / ("oncocompute_mean.exe" if os.name == "nt" else "oncocompute_mean")


class NativeUnavailable(Exception):
    pass


def verified_build() -> dict:
    try:
        build = json.loads((NATIVE / "bin/build.json").read_text(encoding="utf-8"))
        if sha256(BINARY.read_bytes()).hexdigest() != build["binary_sha256"]:
            raise ValueError("Binary has changed")
        for path, digest in build["sources_sha256"].items():
            if sha256((NATIVE / path).read_bytes()).hexdigest() != digest:
                raise ValueError("Source has changed")
        return build
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise NativeUnavailable("OncoCompute needs a build. Run: python scripts/build_oncocompute.py") from exc


def status() -> str:
    try:
        verified_build()
        return "mean adapter built; execution checked when calculating"
    except NativeUnavailable:
        return "mean adapter requires build"


def calculate_mean(values: list[float], unit: str) -> dict:
    if not values or len(values) > 10000 or any(not math.isfinite(v) or abs(v) > 1e100 for v in values):
        raise ValueError("Use 1–10000 finite values with absolute value at most 1e100.")
    build = verified_build()
    payload = str(len(values)) + "\n" + "\n".join(format(v, ".17g") for v in values) + "\n"
    try:
        run = subprocess.run([str(BINARY)], input=payload, capture_output=True, text=True, timeout=5, check=True)
        result = float(run.stdout.strip())
        if not math.isfinite(result):
            raise ValueError("Non-finite result")
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise NativeUnavailable("OncoCompute execution failed. Rebuild the adapter and check the backend.") from exc
    return {
        "operation": "arithmetic_mean",
        "count": len(values),
        "mean": result,
        "unit": unit,
        "inputs": values,
        "provenance": {
            "engine": "OncoCompute C++ oncocompute::mean",
            "adapter_version": "1.0",
            "calculated_at_utc": datetime.now(timezone.utc).isoformat(),
            "native_input_sha256": sha256(payload.encode("ascii")).hexdigest(),
            "build": build,
            "interpretation": "Arithmetic mean on the supplied scale. Units are user-declared, not verified; no concentration conversion, assay pooling validation, or potency estimation is performed.",
        },
    }
