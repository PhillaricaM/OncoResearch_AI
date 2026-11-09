import csv
import io
import json
import math
import os

import httpx
import streamlit as st

st.set_page_config(page_title="OncoResearch AI", page_icon="🔬", layout="wide")
st.title("OncoResearch AI")
st.caption("ChEMBL compound explorer · OncoCompute C++ calculations · Research dashboards")
st.info("Search results are candidate matches. Confirm the ChEMBL identifier before using a compound. OncoCompute arithmetic mean is available after building the native adapter; AI interpretation is not connected yet.")

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
            with st.spinner("Retrieving ChEMBL records… A hosted backend may take about a minute to wake up."):
                response = httpx.get(
                    os.getenv("ONCORESEARCH_API_URL", "http://127.0.0.1:8000").rstrip("/") + "/compounds/search",
                    params={"q": query.strip(), "limit": limit}, timeout=120,
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

st.divider()
st.subheader("OncoCompute · Calculate an arithmetic mean")
st.caption("Runs the C++ mean function on values you supply. Use comparable measurements in the same units and on the same scale. This does not fit a dose-response curve or estimate IC50.")
with st.form("native_mean"):
    mean_values = st.text_area("Values (separated by commas, spaces, or new lines)", "1, 2, 3", max_chars=200000)
    mean_unit = st.text_input("Units or scale", "dimensionless", max_chars=60)
    mean_submitted = st.form_submit_button("Calculate with OncoCompute")

if mean_submitted:
    st.session_state.pop("mean_result", None)
    try:
        numbers = [float(value) for value in mean_values.replace(",", " ").split()]
        if not numbers or len(numbers) > 10000 or any(not math.isfinite(v) or abs(v) > 1e100 for v in numbers):
            raise ValueError("Enter 1–10000 finite numbers with absolute value at most 1e100.")
        if not mean_unit.strip():
            raise ValueError("Enter the units or scale of your values.")
    except ValueError:
        st.error("Enter 1–10000 valid finite numbers (absolute value at most 1e100), and provide their units or scale.")
    else:
        try:
            with st.spinner("Running the OncoCompute C++ calculation… The hosted backend may need time to wake up."):
                mean_response = httpx.post(
                    os.getenv("ONCORESEARCH_API_URL", "http://127.0.0.1:8000").rstrip("/") + "/oncocompute/mean",
                    json={"values": numbers, "unit": mean_unit.strip()}, timeout=120,
                )
                mean_response.raise_for_status()
                st.session_state.mean_result = mean_response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 503:
                st.error("OncoCompute is unavailable. In VS Code, run the native build step from ONCOCOMPUTE.md, then retry.")
            else:
                st.error(f"Calculation failed (HTTP {exc.response.status_code}). Check the backend and retry.")
        except (httpx.HTTPError, ValueError):
            st.error("Cannot reach the calculation service. Check that the backend is running.")

if "mean_result" in st.session_state:
    mean_result = st.session_state.mean_result
    st.metric("Arithmetic mean", format(mean_result["mean"], ".12g"))
    st.caption(f"{mean_result['count']} values · declared unit/scale: {mean_result['unit']}")
    st.write("Inputs used:", mean_result["inputs"])
    with st.expander("Calculation provenance"):
        st.json(mean_result["provenance"])
    st.download_button("Download calculation record (JSON)", json.dumps(mean_result, indent=2), "oncocompute-mean.json", "application/json")

st.divider()
st.subheader("OncoCompute · NCI-60 cancer drug response")
st.caption("Published Tableau dashboard. It uses its own published dataset; ChEMBL searches above do not update or filter it. Viewing it does not run the OncoCompute C++ library.")
tableau_view = (
    "https://public.tableau.com/views/"
    "OncoComputeNCI-60CancerDrugResponseAnalysis/"
    "OncoComputeNCI-60CancerDrugResponseAnalysis"
)
st.link_button("Open dashboard in Tableau Public", tableau_view + "?:showVizHome=no")
if st.toggle("Show Tableau dashboard here", key="show_tableau"):
    st.iframe(
        tableau_view + "?:showVizHome=no&:embed=yes&:tabs=no&:toolbar=yes",
        height=850,
        alt="Published OncoCompute NCI-60 cancer drug response analysis dashboard",
    )
    st.caption("If the dashboard stays blank or Tableau asks you to sign in, use the link above to open it directly.")

st.divider()
st.subheader("PharmaLab · Cancer gene expression")
st.caption("Published Tableau dashboard with its own gene-expression dataset. Compound searches and OncoCompute calculations do not update or filter this dashboard.")
gene_expression_view = (
    "https://public.tableau.com/views/"
    "PharmaLab_Cancer_Gene_Expression/PharmaLabCancerGeneExpressionDashboard"
)
st.link_button("Open gene expression in Tableau Public", gene_expression_view + "?:showVizHome=no")
if st.toggle("Show gene-expression dashboard here", key="show_gene_expression_tableau"):
    st.iframe(
        gene_expression_view + "?:showVizHome=no&:embed=yes&:tabs=no&:toolbar=yes",
        height=850,
        alt="Published PharmaLab cancer gene expression dashboard",
    )
    st.caption("If the dashboard stays blank or Tableau asks you to sign in, use the link above to open it directly.")

st.divider()
st.subheader("PharmaLab · Compound analysis")
st.caption("Published Tableau dashboard with its own compound dataset. ChEMBL searches above do not update or filter this dashboard.")
pharmalab_view = (
    "https://public.tableau.com/views/"
    "PharmaLabScientificAnalyzer_CompoundAnalysis/Dashboard1"
)
st.link_button("Open PharmaLab in Tableau Public", pharmalab_view + "?:showVizHome=no")
if st.toggle("Show PharmaLab dashboard here", key="show_pharmalab_tableau"):
    st.iframe(
        pharmalab_view + "?:showVizHome=no&:embed=yes&:tabs=no&:toolbar=yes",
        height=850,
        alt="Published PharmaLab Scientific Analyzer compound analysis dashboard",
    )
    st.caption("If the dashboard stays blank or Tableau asks you to sign in, use the link above to open it directly.")
