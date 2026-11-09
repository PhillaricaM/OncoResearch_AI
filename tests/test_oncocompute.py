import math
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from streamlit.testing.v1 import AppTest

from backend import oncocompute
from backend.main import app


@pytest.fixture(scope="module")
def native_build():
    if not shutil.which("g++"):
        pytest.skip("Native integration tests require g++ and a real OncoCompute build")
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root / "scripts/build_oncocompute.py")], check=True, cwd=root)


@pytest.mark.parametrize("values", [[1.0, 2.0, 3.0], [-5.1127, -4.0, -4.0, -5.3684, -4.0], [7.5], [-2.0, 2.0], [1e100, 1e100]])
def test_real_cpp_mean_matches_reference(native_build, values):
    with TestClient(app) as client:
        response = client.post("/oncocompute/mean", json={"values": values, "unit": "test scale"})
        assert response.status_code == 200
        result = response.json()
        assert result["mean"] == pytest.approx(math.fsum(values) / len(values), rel=1e-14, abs=1e-14)
        assert result["inputs"] == values
        assert result["unit"] == "test scale"
        assert result["provenance"]["engine"] == "OncoCompute C++ oncocompute::mean"
        assert result["provenance"]["build"]["upstream"]["revision"] == "1c4cb3777f30cc369a955d97eb7e9fd6babb651a"


@pytest.mark.parametrize("values,unit", [([], "Da"), ([True], "Da"), (["abc"], "Da"), ([1e101], "Da"), ([1.0] * 10001, "Da"), ([1.0], " ")])
def test_bad_inputs(values, unit):
    with TestClient(app) as client:
        assert client.post("/oncocompute/mean", json={"values": values, "unit": unit}).status_code == 422


def test_nonfinite_json_rejected():
    with TestClient(app) as client:
        # Strings are also rejected so JSON serialization never has to emit NaN.
        for value in ["NaN", "Infinity", "-Infinity"]:
            assert client.post("/oncocompute/mean", json={"values": [value], "unit": "Da"}).status_code == 422


def test_missing_or_changed_binary_is_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(oncocompute, "BINARY", tmp_path / "missing.exe")
    with TestClient(app) as client:
        response = client.post("/oncocompute/mean", json={"values": [1, 2], "unit": "dimensionless"})
        assert response.status_code == 503
        assert "build" in response.json()["detail"]


def test_native_rejects_invalid_protocol(native_build):
    for payload in ("0\n", "1\nnan\n", "1\n1e101\n", "1\n2\n3\n"):
        result = subprocess.run([str(oncocompute.BINARY)], input=payload, text=True, capture_output=True, timeout=5)
        assert result.returncode != 0


def test_browser_form_runs_real_backend_and_cpp(native_build):
    root = Path(__file__).resolve().parents[1]
    with TestClient(app) as client:
        def post_to_backend(url, *, json, timeout):
            assert url.endswith("/oncocompute/mean")
            return client.post("/oncocompute/mean", json=json)
        with patch("httpx.post", side_effect=post_to_backend):
            page = AppTest.from_file(str(root / "frontend/app.py"), default_timeout=30).run()
            assert not page.exception
            page.button[1].click().run()
            assert not page.exception
            assert page.metric[0].value == "2"
            assert page.session_state["mean_result"]["inputs"] == [1.0, 2.0, 3.0]
            page.text_area[0].set_value("NaN")
            page.button[1].click().run()
            assert len(page.error) == 1
            assert len(page.metric) == 0
