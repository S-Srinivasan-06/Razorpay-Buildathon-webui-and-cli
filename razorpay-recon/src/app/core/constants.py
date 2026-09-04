"""Constants Registry and Parameter Management.

Loads engine thresholds, scoring weights, timeout durations, and fee schedules
from versioned YAML definitions (e.g., constants_v0.yaml). Performs runtime
validation to ensure all weights sum to 1.0 and values stay within valid bounds.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel

from app.core.contracts import FeeSchedule


class Constant(BaseModel):
    """Metadata and constraint definition for a single engine parameter.
    
    Attributes:
        name: Unique identifier for the constant (e.g. 'match_auto_threshold').
        value: Numeric floating-point value assigned to the constant.
        scope: Domain scope such as 'match', 'mapping', 'exception', or 'runtime'.
        derivation_method: Description of how the default was chosen (e.g. 'manual_default').
        derived_from: Source reference or benchmark dataset.
        valid_range: Optional [min, max] inclusive bounding range for validation.
        gates: State gate or component that consumes this parameter.
        unit: Optional unit string (e.g. 'seconds', 'ratio', 'count', 'usd').
    """
    name: str
    value: float
    scope: str
    derivation_method: str = "manual_default"
    derived_from: str
    valid_range: Optional[List[float]] = None
    gates: str
    unit: Optional[str] = None


class Registry:
    """In-memory constants registry loaded from a versioned YAML specification.
    
    Validates range bounds on each parameter and ensures that attribute weights
    for mapping, matching, and exception scoring each sum to 1.000.
    """

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        """Initialize and validate the registry from the specified YAML file.
        
        Args:
            path: Optional path to YAML constants file. Defaults to constants_v0.yaml.
            
        Raises:
            ValueError: If any constant is out of its valid range or if scoring
                weights within any scope do not sum to 1.0.
        """
        if path is None:
            from app.config import BASE_DIR
            path = BASE_DIR / "constants_v0.yaml"

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self.version: str = raw["version"]
        self.loaded_at: datetime = datetime.now()
        self._c: Dict[str, Constant] = {c["name"]: Constant(**c) for c in raw["constants"]}
        self.fee_schedules: Dict[str, FeeSchedule] = {
            fs["schedule_id"]: FeeSchedule(**fs)
            for fs in raw.get("fee_schedules", [])
        }

        # Validate that every constant value falls within its declared valid_range
        for c in self._c.values():
            if c.valid_range and not (c.valid_range[0] <= c.value <= c.valid_range[1]):
                raise ValueError(f"Constant '{c.name}'={c.value} is outside valid range {c.valid_range}")

        # Enforce weight summation invariant (weights must sum to 1.0 for each scoring scope)
        for scope in ("mapping", "match", "exception"):
            ws = [c.value for c in self._c.values() if c.name.startswith(f"w_{scope}_")]
            if ws and abs(sum(ws) - 1.0) > 1e-6:
                raise ValueError(f"Weights for scope '{scope}' sum to {sum(ws)}, expected 1.0")

    def __getitem__(self, k: str) -> float:
        """Retrieve the numeric value of a constant by name."""
        return self._c[k].value


# Global constants registry singleton
REG = Registry()

