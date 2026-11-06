# OncoResearch AI — milestone 1

A local browser research assistant scaffold. Working path: Streamlit → FastAPI → ChEMBL → table, CSV, and downloadable provenance JSON. No model, API key, or AI-generated scientific claim is involved yet.

## Windows / VS Code setup

Open this folder in VS Code using File → Open Folder. Install Microsoft's Python extension. Use Terminal → New Terminal (PowerShell), with this folder as the working directory.

Use Python 3.11 or newer. This computer has a Miniconda interpreter at `C:\Users\phill\miniconda3\python.exe`; the usual `python` command currently points to an unusable Windows app alias. Create an isolated environment:

```powershell
& C:\Users\phill\miniconda3\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If environment creation fails at `ensurepip`, but `.venv\Scripts\python.exe --version` works, bootstrap packages with the existing Miniconda pip:

```powershell
& C:\Users\phill\miniconda3\python.exe -m pip --python .\.venv\Scripts\python.exe install -r requirements.txt
```

In VS Code, press Ctrl+Shift+P → Python: Select Interpreter → Enter interpreter path → select `.venv\Scripts\python.exe`. These commands use the interpreter explicitly, so PowerShell activation and execution-policy changes are unnecessary.

Start the backend in the first terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open a second terminal in the same folder and start the frontend:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501, search `aspirin`, and inspect candidate identifiers. Download both the table and research record. Actual counts and descriptors may change with ChEMBL. API documentation is at http://127.0.0.1:8000/docs; health is at http://127.0.0.1:8000/health. Stop each process with Ctrl+C. Keep this unauthenticated milestone bound to localhost.

Optional backend location override: set `$env:ONCORESEARCH_API_URL = 'http://127.0.0.1:8000'` before starting Streamlit.

## How the code works

* `frontend/app.py` collects the query in a form, calls the backend only on submission, and displays results. Session state keeps downloads available across Streamlit reruns. A new search clears previous results before making a request.
* `backend/main.py` defines HTTP routes, validates query length and result limits, and maps upstream failures to HTTP 502. FastAPI manages a shared HTTP client during application startup/shutdown.
* `backend/chembl.py` adapts PharmaLab's existing ChEMBL workflow into `search(query, limit)`. It returns source descriptors without calculating potency or ranking therapeutic benefit. External requests have a timeout.
* `backend/integrations.py` defines interfaces (Python Protocols). A provider can be replaced without changing the route or frontend. The dose-response interface is a proposal, not a working OncoCompute binding.
* `tests/test_search.py` substitutes an in-memory ChEMBL service to test validation, missing values, empty searches, provenance, timeouts, and malformed upstream responses without internet access.

## Scientific provenance and limits

Each JSON download contains the query, exact requested source URL, UTC retrieval time, limits and total match count, application and transformation versions, raw ChEMBL response, and a SHA-256 digest of the original HTTP response bytes. `raw_response_base64` preserves those bytes exactly: base64-decode that field and hash the result to verify the digest. The parsed `raw_response` is convenient for inspection. Archive the downloaded record with your research outputs. The application does not persist searches on the server.

Only the first requested page is fetched (maximum 20). `truncated` flags additional matches. Missing descriptors remain null, never zero. Source numeric strings are retained, avoiding silent rounding. CSV is a display export: empty cells represent missing values and formula-like strings are escaped; JSON is the research record. Molecular weight is reported in Da, polar surface area in Å², ALogP is dimensionless. The database release is explicitly unknown because it is not included in the search response. An archived response supports inspection of that query, but does not pin the full ChEMBL database.

Search matches may include synonyms, salts, or related compounds. A name match is not identity confirmation. These descriptors alone do not establish cancer relevance, assay potency, safety, or clinical efficacy. No bioactivity pooling or IC50 estimation is performed in this slice.

## Existing project integration status

Reviewed on 2026-11-05:

* PharmaLab source: `C:\Users\phill\OneDrive\Documents\Data Science\Projects\Pharmalab_Analyzer\src\compound_lookup.py` and `molecular_properties.py`. Their requests/search/descriptor extraction logic is adapted here. Those files currently perform network requests and printing at import time, so this app deliberately does not import them. Existing files were not modified. Next: extract these functions into an installable PharmaLab package, preserve its existing script behavior under `if __name__ == '__main__':`, and implement `CompoundProvider` with that package.
* The available `C ++ Projects` folder contained `helloworld.cpp`, not an OncoCompute scientific API. OncoCompute is not connected. Once its source is available, review the public functions, units, compiler/build configuration, and tests before implementing a binding (for example pybind11). Never substitute a fake calculation labeled as OncoCompute.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Optional live smoke check with the backend running (requires internet):

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/compounds/search?q=aspirin&limit=5'
```

After setup succeeds, record exact versions for reproducibility:

```powershell
.\.venv\Scripts\python.exe -m pip freeze > requirements-lock.txt
```

`requirements-lock.txt` records the installed versions verified on Windows with Python 3.14.6. For the same pinned dependencies, install with `-r requirements-lock.txt` instead of `-r requirements.txt`. Do not copy PharmaLab's environment wholesale.

Verified on 2026-11-05: all five tests passed, including the Streamlit form submission/table display test. A live FastAPI request through TestClient retrieved aspirin (`CHEMBL25`) from ChEMBL and verified the downloaded response bytes against the SHA-256 digest. The upstream TestClient library emits an httpx deprecation warning; it does not affect these passing checks. A manual browser layout review has not been performed.

## Incremental next steps

1. Complete and verify this compound search slice.
2. Package the real PharmaLab functions and add known-value regression fixtures.
3. Connect OncoCompute with explicit concentration/response units, invalid-input handling, and independently checked numerical results.
4. Add compound selection by ChEMBL ID and assay-aware activity retrieval before any comparison of potency.
5. Add natural-language tool selection. Keep model interpretation separate from tool results and attach source records to claims.

## Primary references

* ChEMBL services: https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services
* FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
* Streamlit installation: https://docs.streamlit.io/get-started/installation
