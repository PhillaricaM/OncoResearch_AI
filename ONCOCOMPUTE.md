# OncoCompute calculation integration

The app now calls the real C++ `oncocompute::mean` function through a compiled command-line adapter. FastAPI sends numbers over standard input, runs a fixed executable with a five-second timeout, and returns the calculated mean and a research record. No shell commands or user-selected executable paths are accepted from the browser. There is no Python fallback.

## Build once on Windows

Open this project folder in VS Code. The compiler found on this computer is MSYS2 UCRT64 g++ at `C:\msys64\ucrt64\bin\g++.exe`. If g++ is not already on your terminal's PATH, add its directory for this terminal:

```powershell
$env:Path = "C:\msys64\ucrt64\bin;" + $env:Path
```

Then run:

```powershell
.\.venv\Scripts\python.exe scripts/build_oncocompute.py
```

The script compiles C++20, checks a real calculation, and creates `backend/native/bin/` with the executable and build manifest. Generated binaries are excluded from Git; rebuild on each new computer. The Windows binary is statically linked to avoid requiring MSYS2 runtime DLLs in the API process. On Linux the same script uses g++ on PATH.

## Run in the browser

Start the usual FastAPI and Streamlit processes in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501, scroll to **OncoCompute · Calculate an arithmetic mean**, enter `1, 2, 3` with unit `dimensionless`, and click **Calculate with OncoCompute**. The expected mean is `2`. Download the calculation JSON to retain its inputs and provenance.

The API also accepts `POST /oncocompute/mean` with:

```json
{"values": [1, 2, 3], "unit": "dimensionless"}
```

## Scope and scientific limits

Only arithmetic mean is connected. Dose-response fitting and IC50 estimation are not implemented in the reviewed upstream version. Units and scale are supplied by the user; the software does not verify assay comparability or convert concentrations. The mean of logarithmic values remains on that logarithmic scale and must not be labeled an arithmetic mean of linear concentrations. No supplied default numbers represent experimental measurements.

The adapter accepts 1–10000 finite numbers with absolute value at most 1e100. These limits prevent overflow of the naive double-precision sum used by the upstream implementation. That implementation can still lose precision with very different magnitudes or cancellation; this integration does not upgrade its numerical method. Validate suitability before scientific use.

The Tableau dashboards remain independently published views. This calculation does not update them, and their datasets are not automatically passed into this form.

## Source and provenance

Reviewed source: https://github.com/PhillaricaM/OncoCompute/tree/1c4cb3777f30cc369a955d97eb7e9fd6babb651a

`backend/native/upstream/` contains a reviewed snapshot of `src/statistics.cpp` and `include/oncocompute/statistics.hpp`. Their calculation logic is unchanged. The bridge is separate in `mean_bridge.cpp`. The original OncoCompute repository is not modified.

Each result includes the upstream revision, compiler version, build flags, hashes of the source files and executable, inputs, user-declared unit, UTC calculation time, adapter version, and native input checksum. The backend checks build hashes before each execution and returns HTTP 503 when the build is missing or stale. Archive the calculation JSON; calculations are not persisted on the server.

## Updating as OncoCompute develops

1. Commit and test the new calculation in OncoCompute first.
2. Review its inputs, units, error behavior, and independently checked expected results.
3. Update the reviewed snapshot and `SOURCE.json` to the exact upstream revision.
4. Extend the bridge, API, UI, and tests for the new operation.
5. Rebuild and run `.\.venv\Scripts\python.exe -m pytest -q`.
6. Commit the integration changes to OncoResearch AI. Do not commit compiled binaries.

This deliberately pins a known source version instead of silently pulling upstream changes. Existing calculations remain traceable while the projects develop independently.

## Future hosting

Hosting remains deferred. A future backend deployment must run `python scripts/build_oncocompute.py` during its build and provide g++. Streamlit only talks to the backend; it does not need the compiler. The deployment files include this build step, but no service is deployed by these changes.
