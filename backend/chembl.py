"""Callable adaptation of PharmaLab's compound_lookup/molecular_properties scripts.

No requests run on import. Original scripts remain untouched.
"""
from base64 import b64encode
from datetime import datetime, timezone
from hashlib import sha256

import httpx

BASE = "https://www.ebi.ac.uk/chembl/api/data"


class UpstreamError(Exception):
    pass


class ChEMBLProvider:
    def __init__(self, client: httpx.Client):
        self.client = client

    def search(self, query: str, limit: int) -> dict:
        try:
            response = self.client.get(
                f"{BASE}/molecule/search.json", params={"q": query, "limit": limit}
            )
            response.raise_for_status()
            raw = response.json()
            molecules = raw["molecules"]
            total = raw["page_meta"]["total_count"]
            if not isinstance(molecules, list) or not isinstance(total, int):
                raise ValueError("Invalid search response")
            rows = []
            for molecule in molecules:
                properties = molecule.get("molecule_properties") or {}
                rows.append({
                    "chembl_id": molecule["molecule_chembl_id"],
                    "compound_name": molecule.get("pref_name"),
                    "molecular_formula": properties.get("full_molformula"),
                    "molecular_weight_da": properties.get("full_mwt"),
                    "alogp": properties.get("alogp"),
                    "polar_surface_area_a2": properties.get("psa"),
                })
        except httpx.TimeoutException as exc:
            raise UpstreamError("ChEMBL timed out. Please retry.") from exc
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise UpstreamError("ChEMBL is unavailable or returned an unexpected response.") from exc

        return {
            "compounds": rows,
            "provenance": {
                "schema_version": "1.0",
                "application_version": "0.1.0",
                "provider": "ChEMBL",
                "source_url": str(response.url),
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "query": query,
                "limit": limit,
                "total_matches": total,
                "returned_count": len(rows),
                "truncated": total > len(rows),
                "raw_response_sha256": sha256(response.content).hexdigest(),
                "normalization": "pharmalab-compound-fields-v1; missing values preserved as null",
                "database_release": None,
                "database_release_note": "Not supplied by this search endpoint; raw response retained.",
                "interpretation": "Search matches and database descriptors only; no efficacy inference.",
            },
            "raw_response": raw,
            "raw_response_base64": b64encode(response.content).decode("ascii"),
        }
