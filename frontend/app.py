import csv
import io
import json
import os

import httpx
import streamlit as st

st.set_page_config(page_title="OncoResearch AI", page_icon="🔬", layout="wide")
st.title("OncoResearch AI")
st.caption("Milestone 1 · ChEMBL compound explorer · PharmaLab workflow")
st.info("Search results are candidate matches. Confirm the ChEMBL identifier before using a compound. AI interpretation and OncoCompute are not connected yet.")

with st.form("search"):
    query = st.text_input("Compound name", "aspirin", max_chars=120)
    limit = st.slider("Maximum matches", 1, 20, 5)
    submitted = st.form_submit_button("Search ChEMBL")

if submitted:
    st.session_state.pop("result", None)
    if not query.strip():
        st.warning("Enter a compound name.")
    else:
        try:
            with st.spinner("Retrieving ChEMBL records…"):
                response = httpx.get(
                    os.getenv("ONCORESEARCH_API_URL", "http://127.0.0.1:8000").rstrip("/") + "/compounds/search",
                    params={"q": query.strip(), "limit": limit}, timeout=30,
                )
                response.raise_for_status()
                st.session_state.result = response.json()
        except httpx.HTTPStatusError as exc:
            st.error(f"Search failed (HTTP {exc.response.status_code}). Check the backend and retry.")
        except (httpx.HTTPError, ValueError):
            st.error("Cannot retrieve results. Check that the backend is running, then retry.")

if "result" in st.session_state:
    result = st.session_state.result
    rows = result["compounds"]
    provenance = result["provenance"]
    st.write(f"Query: {provenance['query']} · {len(rows)} of {provenance['total_matches']} matches shown")
    if rows:
        st.dataframe(rows, hide_index=True)
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        # Prevent spreadsheet formula execution when opening external text in CSV.
        for row in rows:
            writer.writerow({key: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value for key, value in row.items()})
        st.download_button("Download table (CSV)", output.getvalue(), "compounds.csv", "text/csv")
    else:
        st.warning("No matches. Try another compound name.")
    st.caption("Molecular weight: Da; polar surface area: Å²; ALogP: dimensionless. Missing properties remain empty. Values are reported as supplied by ChEMBL.")
    with st.expander("Scientific provenance"):
        st.json(provenance)
    st.download_button("Download research record (JSON)", json.dumps(result, indent=2), "research-record.json", "application/json")
