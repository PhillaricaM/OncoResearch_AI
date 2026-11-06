import base64
import hashlib

import httpx
from fastapi.testclient import TestClient

from backend.chembl import ChEMBLProvider
from backend.main import app, get_provider


def client_for(handler):
    upstream = httpx.Client(transport=httpx.MockTransport(handler))
    app.dependency_overrides[get_provider] = lambda: ChEMBLProvider(upstream)
    return upstream, TestClient(app)


def test_search_preserves_missing_values_and_evidence():
    body = b'{"molecules":[{"molecule_chembl_id":"CHEMBL25","pref_name":"ASPIRIN","molecule_properties":null}],"page_meta":{"total_count":8}}'
    def handler(request):
        assert request.url.params["q"] == "aspirin"
        return httpx.Response(200, content=body)
    upstream, client = client_for(handler)
    try:
        with upstream, client:
            response = client.get("/compounds/search", params={"q": " aspirin "})
            assert response.status_code == 200
            result = response.json()
            assert result["compounds"][0]["molecular_weight_da"] is None
            assert result["provenance"]["truncated"] is True
            assert result["provenance"]["raw_response_sha256"] == hashlib.sha256(body).hexdigest()
            assert base64.b64decode(result["raw_response_base64"]) == body
            assert result["raw_response"]["molecules"][0]["molecule_chembl_id"] == "CHEMBL25"
    finally:
        app.dependency_overrides.clear()


def test_descriptor_mapping_keeps_source_precision():
    record = {"molecule_chembl_id": "CHEMBL25", "pref_name": "ASPIRIN", "molecule_properties": {"full_molformula": "C9H8O4", "full_mwt": "180.16", "alogp": "1.31", "psa": "63.60"}}
    upstream, client = client_for(lambda r: httpx.Response(200, json={"molecules": [record], "page_meta": {"total_count": 1}}))
    try:
        with upstream, client:
            result = client.get("/compounds/search?q=aspirin").json()
            assert result["compounds"][0] == {"chembl_id": "CHEMBL25", "compound_name": "ASPIRIN", "molecular_formula": "C9H8O4", "molecular_weight_da": "180.16", "alogp": "1.31", "polar_surface_area_a2": "63.60"}
            assert result["provenance"]["truncated"] is False
    finally:
        app.dependency_overrides.clear()


def test_input_validation_and_empty_results():
    upstream, client = client_for(lambda request: httpx.Response(200, json={"molecules": [], "page_meta": {"total_count": 0}}))
    try:
        with upstream, client:
            for params in ({"q": " "}, {"q": "a", "limit": 21}, {"q": "a", "limit": 0}, {}):
                assert client.get("/compounds/search", params=params).status_code == 422
            assert client.get("/compounds/search?q=unknown").json()["compounds"] == []
    finally:
        app.dependency_overrides.clear()


def test_upstream_failures():
    def timeout(request):
        raise httpx.ReadTimeout("timeout", request=request)
    for handler in (timeout, lambda r: httpx.Response(503), lambda r: httpx.Response(200, text="invalid"), lambda r: httpx.Response(200, json={})):
        upstream, client = client_for(handler)
        try:
            with upstream, client:
                assert client.get("/compounds/search?q=aspirin").status_code == 502
        finally:
            app.dependency_overrides.clear()
