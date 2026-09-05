"""Constants Registry and Parameter Management.

Provides engine thresholds, scoring weights, timeout durations, and fee schedules
embedded directly in Python, with optional loading from versioned YAML files. Performs
runtime validation to ensure all weights sum to 1.0 and values stay within valid bounds.
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


DEFAULT_CONSTANTS_SPEC: Dict[str, Any] = {
    "version": "v0",
    "constants": [
        {"name": "mapping_auto_accept", "value": 0.70, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.50, 0.90], "gates": "MAPPING_VALIDATED auto-accept"},
        {"name": "mapping_review_floor", "value": 0.40, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.20, 0.60], "gates": "MAPPING_VALIDATED halt"},
        {"name": "mapping_ambiguity_delta", "value": 0.10, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.05, 0.20], "gates": "escalate-to-user"},
        {"name": "match_auto_threshold", "value": 0.85, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.70, 0.95], "gates": "auto-match"},
        {"name": "match_review_floor", "value": 0.60, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.40, 0.80], "gates": "below=reject, band=review"},
        {"name": "w_mapping_structural", "value": 0.35, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "mapping_confidence"},
        {"name": "w_mapping_sample", "value": 0.30, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "mapping_confidence"},
        {"name": "w_mapping_type", "value": 0.20, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "mapping_confidence"},
        {"name": "w_mapping_semantic", "value": 0.15, "scope": "MAPPING", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "mapping_confidence"},
        {"name": "w_match_key", "value": 0.40, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "match_confidence"},
        {"name": "w_match_amount", "value": 0.30, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "match_confidence"},
        {"name": "w_match_date", "value": 0.20, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "match_confidence"},
        {"name": "w_match_semantic", "value": 0.10, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "v3 weights, unvalidated", "valid_range": [0.0, 1.0], "gates": "match_confidence"},
        {"name": "w_exception_evidence", "value": 0.50, "scope": "EXCEPTION", "derivation_method": "manual_default", "derived_from": "v0 renormalized", "valid_range": [0.0, 1.0], "gates": "exception_confidence"},
        {"name": "w_exception_category", "value": 0.30, "scope": "EXCEPTION", "derivation_method": "manual_default", "derived_from": "v0 renormalized", "valid_range": [0.0, 1.0], "gates": "exception_confidence"},
        {"name": "w_exception_semantic", "value": 0.20, "scope": "EXCEPTION", "derivation_method": "manual_default", "derived_from": "v0 renormalized", "valid_range": [0.0, 1.0], "gates": "exception_confidence"},
        {"name": "exception_auto_resolve_confidence", "value": 0.85, "scope": "EXCEPTION", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.70, 0.95], "gates": "auto_resolve"},
        {"name": "exception_auto_resolve_evidence_min", "value": 2.0, "scope": "EXCEPTION", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [1.0, 5.0], "gates": "auto_resolve"},
        {"name": "pii_mask_threshold", "value": 0.70, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.50, 0.90], "gates": "auto-mask"},
        {"name": "pii_review_threshold", "value": 0.40, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.20, 0.60], "gates": "review flag"},
        {"name": "revision_match_rate_threshold", "value": 0.60, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.40, 0.80], "gates": "REVISION entry"},
        {"name": "revision_iteration_cap", "value": 3.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed cap", "gates": "REVISION loop"},
        {"name": "revision_time_cap_s", "value": 120.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed cap", "gates": "REVISION loop", "unit": "s"},
        {"name": "revision_cost_cap_usd", "value": 0.10, "scope": "pipeline", "derivation_method": "derived", "derived_from": "20x single-revision cost", "gates": "REVISION loop", "unit": "usd"},
        {"name": "regression_reject_delta", "value": 0.05, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.02, 0.10], "gates": "safe-revision gate"},
        {"name": "circuit_breaker_failure_count", "value": 3.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "per-tool HALT"},
        {"name": "calibration_sanity_floor", "value": 0.50, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "reasoned default", "valid_range": [0.30, 0.80], "gates": "CALIBRATION_DRIFT_WARNING"},
        {"name": "ingest_timeout_s_per_file", "value": 60.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "INGESTING", "unit": "s"},
        {"name": "profiling_timeout_s_per_table", "value": 30.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "PROFILING", "unit": "s"},
        {"name": "dry_run_timeout_s", "value": 20.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "DRY_RUN", "unit": "s"},
        {"name": "sandbox_timeout_s", "value": 30.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "EXECUTING", "unit": "s"},
        {"name": "sandbox_memory_mb", "value": 512.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "sandbox", "unit": "mb"},
        {"name": "llm_tool_timeout_s", "value": 25.0, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "fixed", "gates": "tool calls", "unit": "s"},
        {"name": "cost_llm_in_per_1k_usd", "value": 0.0005, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "provider list price", "gates": "CostTracker", "unit": "usd"},
        {"name": "cost_llm_out_per_1k_usd", "value": 0.0015, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "provider list price", "gates": "CostTracker", "unit": "usd"},
        {"name": "cost_sandbox_cpu_s_usd", "value": 0.00001, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "provider list price", "gates": "CostTracker", "unit": "usd"},
        {"name": "cost_sandbox_mem_gb_s_usd", "value": 0.000005, "scope": "pipeline", "derivation_method": "manual_default", "derived_from": "provider list price", "gates": "CostTracker", "unit": "usd"},
        {"name": "session_cost_cap_usd", "value": 0.50, "scope": "pipeline", "derivation_method": "derived", "derived_from": "5x revision_cost_cap_usd", "valid_range": [0.10, 5.00], "gates": "CostTracker pre-call", "unit": "usd"},
        {"name": "amount_score_scale_pct", "value": 0.05, "scope": "MATCH", "derivation_method": "manual_default", "derived_from": "5% of gross decay band", "valid_range": [0.01, 0.20], "gates": "amount_delta_score"},
    ],
    "fee_schedules": [
        {
            "provider": "razorpay",
            "schedule_id": "razorpay_test_mode",
            "version": "1.0",
            "effective_from": "2026-01-01",
            "model_type": "flat_rate",
            "params": {"rate": 0.02},
            "gst_rate": 0.18,
            "currency": "INR",
        }
    ],
}


class Registry:
    """In-memory constants registry loaded with robust built-in defaults or from YAML.
    
    Validates range bounds on each parameter and ensures that attribute weights
    for mapping, matching, and exception scoring each sum to 1.000.
    """

    def __init__(self, path: Optional[Union[str, Path]] = None) -> None:
        """Initialize and validate the registry.
        
        Args:
            path: Optional path to YAML constants file. If None or not found,
                falls back to built-in DEFAULT_CONSTANTS_SPEC.
        """
        raw: Dict[str, Any] = DEFAULT_CONSTANTS_SPEC
        if path is not None and Path(path).is_file():
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict) and "constants" in loaded:
                    raw = loaded

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
