"""Contracts for future reusable PharmaLab and OncoCompute packages."""
from typing import Protocol


class CompoundProvider(Protocol):
    def search(self, query: str, limit: int) -> dict: ...


class DoseResponseEngine(Protocol):
    # Implement only after OncoCompute's actual API and units are reviewed.
    def fit(self, concentrations_molar: list[float], responses: list[float]) -> dict: ...
