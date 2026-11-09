# OncoResearch AI

**A browser-based scientific research application connecting compound discovery, C++ calculations, and research visualization.**

OncoResearch AI brings together work from **PharmaLab Analyzer** and **OncoCompute** in one research interface. It currently supports live ChEMBL compound searches, a real OncoCompute C++ arithmetic-mean calculation, downloadable research records, and two published Tableau dashboards.

The long-term goal is an AI-assisted workspace where natural-language questions guide tested scientific tools and produce traceable results. **AI chat and natural-language tool selection are planned and are not implemented in the current release.**

## How the projects fit together

| Project | Purpose | Current connection |
|---|---|---|
| PharmaLab Analyzer | Compound retrieval and analysis in Python | Its ChEMBL search and molecular-property workflow is adapted into backend functions, and its published dashboard is embedded. |
| OncoCompute | Scientific computing and data processing in C++ | Its arithmetic-mean function runs through a compiled adapter, and its NCI-60 dashboard is embedded. |
| OncoResearch AI | Research interface and workflow coordination | Streamlit collects inputs, FastAPI handles requests, and the application displays results with downloadable provenance. |

The projects can develop independently. Integrations use reviewed source versions so changes can be tested before being introduced into the application.

## What we have added

### Live ChEMBL compound exploration

Users can search by compound name and inspect ChEMBL identifiers, names, molecular formulas, molecular weights, ALogP, and polar surface area.

The interface shows how many matches are displayed and preserves missing properties without replacing them with zero. Results can be downloaded as a CSV table and a JSON research record containing source evidence.

This extends PharmaLab's standalone retrieval workflow into a browser application. Direct integration with a reusable PharmaLab Python package remains a future step.

### Real OncoCompute C++ calculations

The application now calls the existing C++ arithmetic-mean function through FastAPI. Users enter numeric values and declare their units or scale, then view the calculated result.

The connection includes input validation, a compiled C++20 adapter, checks for missing or changed builds, and a downloadable calculation record. For example, entering **1, 2, 3** returns an arithmetic mean of **2**.

Calculation records retain the inputs, declared units, source revision, compiler details, and source and executable hashes. Only arithmetic mean is connected at present; dose-response fitting and IC50 estimation remain future work.

### Integrated Tableau dashboards

Two published dashboards can be explored within the application or opened directly:

- [OncoCompute — NCI-60 Cancer Drug Response Analysis](https://public.tableau.com/views/OncoComputeNCI-60CancerDrugResponseAnalysis/OncoComputeNCI-60CancerDrugResponseAnalysis?:showVizHome=no)
- [PharmaLab Scientific Analyzer — Compound Analysis](https://public.tableau.com/views/PharmaLabScientificAnalyzer_CompoundAnalysis/Dashboard1?:showVizHome=no)

Each dashboard retains its own published dataset. Compound searches and calculations do not automatically filter or refresh either dashboard.

### Scientific provenance and testability

Data retrieval, calculation execution, and presentation are organized into separate modules so each can be tested and extended.

ChEMBL research records preserve the requested source URL, query, retrieval time, original response bytes, and checksum. Calculation records preserve the submitted values, declared units, calculation time, and native build information.

On **November 8, 2026**, local verification passed **20 automated tests**, including the browser form calling FastAPI and the real C++ executable. A running-application check also confirmed that the sample calculation displays **2**. Native integration tests require a C++ compiler and are skipped when it is unavailable.

## Current architecture

| Layer | Technology | Responsibility |
|---|---|---|
| Browser interface | Streamlit | Inputs, results, downloads, and dashboard views |
| Backend | FastAPI and HTTPX | Request validation, ChEMBL retrieval, and calculation coordination |
| Numerical computation | OncoCompute C++20 | Arithmetic-mean calculation through a native adapter |
| Visualization | Tableau Public | Published PharmaLab and OncoCompute dashboards |
| Verification | pytest and Streamlit AppTest | Backend, interface, and native integration checks |

## Where the project is going

### Next: expand the scientific tools

- Package reusable PharmaLab functions and connect them through the provider interface.
- Expand OncoCompute with tested statistics such as median and standard deviation.
- Add new calculation operations to the API and browser as their C++ implementations become available.
- Introduce structured dataset inputs with explicit units, scales, and validation rules.

### Then: connect research workflows

- Select compounds by confirmed ChEMBL identifiers.
- Retrieve bioactivity data while retaining assay, target, measurement, and source context.
- Develop dose-response modeling after reviewing suitable datasets and independently checking numerical results.
- Define an explicit export and refresh workflow for Tableau datasets.

### Longer term: introduce AI-assisted orchestration

- Let users describe supported research tasks in natural language.
- Route requests to tested retrieval and calculation tools.
- Clearly distinguish source data, calculated results, and model-generated interpretation.
- Attach supporting research records to summaries and reports.

These are development goals, not features available today.

## Growing the projects together

New calculations will first be developed and tested in OncoCompute, then connected to OncoResearch AI with defined inputs, units, error handling, and reference results. PharmaLab capabilities will follow the same incremental approach.

Source versions are pinned deliberately rather than updated silently. This keeps previous results traceable while the projects continue to develop independently.

Implementation and build details are maintained separately in the [OncoCompute integration guide](ONCOCOMPUTE.md).

## Scientific scope and limitations

This is an educational and portfolio-oriented application under active development. It is not a clinically validated medical decision-support system.

- Compound-name matches require identity confirmation using the identifier and source record.
- Molecular descriptors alone do not establish cancer relevance, potency, safety, or clinical efficacy.
- Calculation units are user-declared; the application does not verify assay comparability or convert concentration scales.
- Means are calculated on the supplied scale. The upstream double-precision summation has numerical precision limits documented in the integration guide.
- The ChEMBL search response does not identify its database release; downloaded records explicitly retain this limitation.
- Research downloads do not archive Tableau datasets. Search and calculation records are not persisted on the server.

## Public demo status

The application currently runs locally. Public hosting is planned; deployment preparation is documented separately in the [deployment guide](DEPLOYMENT.md). A public GitHub repository provides access to the code but does not itself host the running application.

## Related project

- [OncoCompute source repository](https://github.com/PhillaricaM/OncoCompute)
