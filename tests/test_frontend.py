from pathlib import Path
from unittest.mock import patch

import httpx
from streamlit.testing.v1 import AppTest


def test_search_form_displays_backend_results():
    result = {"compounds": [{"chembl_id": "CHEMBL25", "compound_name": "ASPIRIN"}], "provenance": {"query": "aspirin", "total_matches": 1}}
    response = httpx.Response(200, json=result, request=httpx.Request("GET", "http://127.0.0.1:8000/compounds/search"))
    with patch("httpx.get", return_value=response) as fetch:
        page = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "app.py"), default_timeout=30).run()
        assert not page.exception
        assert not fetch.called
        page.button[0].click().run()
        assert not page.exception
        assert len(page.dataframe) == 1
        assert page.dataframe[0].value.iloc[0]["chembl_id"] == "CHEMBL25"
        assert fetch.call_args.kwargs["params"] == {"q": "aspirin", "limit": 5}
