"""Data Contracts and Schema Specifications.

Defines Pydantic data models, strongly typed enums, event payloads, and
decision records governing communication between the state machine, match engine,
LLM tools, event bus, and audit logging.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class MessageKind(str, Enum):
    """Categories of messages transmitted across the event routing bus."""
    CHAT = "chat"
    ARTIFACT = "artifact"
    TRACE = "trace"
    CONTROL = "control"


class ConfidenceScope(str, Enum):
    """Scoring domain for confidence evaluation."""
    MAPPING = "mapping"
    MATCH = "match"
    EXCEPTION = "exception"


class Actor(str, Enum):
    """Entity originating or executing a decision."""
    LLM = "llm"
    USER = "user"
    SYSTEM = "system"
    FALLBACK = "fallback"


class EvidencePiece(str, Enum):
    """Discrete verified evidence elements supporting a match or resolution."""
    KEY_MATCH = "key_match"
    AMOUNT_WITHIN_TOL = "amount_within_tol"
    DATE_WITHIN_WINDOW = "date_within_window"
    FEE_MODEL_MATCH = "fee_model_match"


class HypothesisCategory(str, Enum):
    """Taxonomy of discrepancy root causes for unmatched records."""
    DUPLICATE = "duplicate"
    SPLIT = "split"
    PARTIAL_PAYMENT = "partial_payment"
    REFUND_OFFSET = "refund_offset"
    FEE_DEDUCTION = "fee_deduction"
    TAX_WITHHOLDING = "tax_withholding"
    CURRENCY_CONVERSION = "currency_conversion"
    TEMPORAL_DRIFT = "temporal_drift"
    COUNTERPARTY_MISMATCH = "counterparty_mismatch"
    AMOUNT_DELTA = "amount_delta"
    UNCLASSIFIED = "unclassified"


# Precedence order used when evaluating multiple competing discrepancy hypotheses
HYPOTHESIS_PRIORITY: Dict[HypothesisCategory, int] = {
    HypothesisCategory.DUPLICATE: 1,
    HypothesisCategory.SPLIT: 2,
    HypothesisCategory.PARTIAL_PAYMENT: 3,
    HypothesisCategory.REFUND_OFFSET: 4,
    HypothesisCategory.FEE_DEDUCTION: 5,
    HypothesisCategory.TAX_WITHHOLDING: 6,
    HypothesisCategory.CURRENCY_CONVERSION: 7,
    HypothesisCategory.TEMPORAL_DRIFT: 8,
    HypothesisCategory.COUNTERPARTY_MISMATCH: 9,
    HypothesisCategory.AMOUNT_DELTA: 10,
    HypothesisCategory.UNCLASSIFIED: 11,
}


class MatchComponent(str, Enum):
    """Individual match policy scoring components."""
    EXACT_KEY = "exact_key"
    EXACT_AMOUNT = "exact_amount"
    DATE_WINDOW = "date_window"
    AMOUNT_TOL = "amount_tol"
    CURRENCY_NORM = "currency_norm"
    DUP_DETECT = "dup_detect"
    SPLIT_DETECT = "split_detect"
    FUZZY_KEY = "fuzzy_key"
    SEMANTIC_HINT = "semantic_hint"


class ChatPayload(BaseModel):
    """Payload schema for user and assistant chat messages."""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=2000, description="Message text content")


class ArtifactPayload(BaseModel):
    """Payload schema for generated data artifacts, grids, and summary cards."""
    kind: str = Field(description="Artifact type identifier (e.g. 'report', 'exceptions')")
    schema_version: str = "1.0"
    rows: Optional[List[Dict[str, Any]]] = None
    summary: Dict[str, Any] = {}
    confidence_threshold: float
    fallback_events: List[str] = []


class TracePayload(BaseModel):
    """Payload schema for internal execution trace events and telemetry."""
    event: str
    detail: Dict[str, Any] = {}


class ControlPayload(BaseModel):
    """Payload schema for state machine control signals, halts, and abort tokens."""
    event: str
    state: Optional[str] = None
    abort_token: Optional[str] = None
    detail: Dict[str, Any] = {}


# Registry mapping message kinds to their respective Pydantic validation schemas
SCHEMAS: Dict[MessageKind, Type[BaseModel]] = {
    MessageKind.CHAT: ChatPayload,
    MessageKind.ARTIFACT: ArtifactPayload,
    MessageKind.TRACE: TracePayload,
    MessageKind.CONTROL: ControlPayload,
}


class ToolCall(BaseModel):
    """Configuration for an LLM-invoked tool with schemas, timeouts, and fallback handler."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    args_schema: Type[BaseModel]
    result_schema: Type[BaseModel]
    timeout_s: float
    retries: int
    fallback: Callable[..., Any]
    cost_budget_usd: float


class FeeSchedule(BaseModel):
    """Payment gateway or aggregator fee schedule configuration."""
    provider: str
    schedule_id: str
    version: str
    effective_from: date
    effective_until: Optional[date] = None
    model_type: str  # e.g., 'flat_rate', 'per_txn_flat', 'tiered'
    params: Dict[str, Any]
    gst_rate: float = 0.0
    currency: str = "INR"
    tds_rate: float = 0.01
    fx_corridor_min: float = 0.010
    fx_corridor_max: float = 0.015


class ConfidenceScore(BaseModel):
    """Structured confidence calculation score with sub-component breakdowns."""
    scope: ConfidenceScope
    value: float = Field(ge=0, le=1)
    components: Dict[str, float]
    constants_version: str
    constants_loaded_at: datetime


class DecisionRecord(BaseModel):
    """Immutable audit record representing a discrete engine or operator decision."""
    decision_id: str
    ts: datetime
    state: str
    actor: Actor
    decision_kind: str
    proposal: Dict[str, Any]
    final: Dict[str, Any]
    overridden: bool = False
    override_reason: Optional[str] = None
    confidence: float
    evidence: List[EvidencePiece]
    fallback_used: Optional[str] = None


class ColumnProfile(BaseModel):
    """Statistical and semantic profile of an ingested table column."""
    name: str
    dtype: str
    numeric_ratio: float
    date_ratio: float
    cardinality: float
    null_rate: float
    min_len: int
    max_len: int
    sample_values: List[str]
    pii_likelihood: float


class PolicyComponent(BaseModel):
    """Configured component within a reconciliation matching policy."""
    component: MatchComponent
    params: Dict[str, Any]
    enabled: bool = True
    precedence: int


class Policy(BaseModel):
    """Complete synthesized matching policy specification."""
    components: List[PolicyComponent]
    generated_from: str = "deterministic_library_v0"
    revision_history: List[Dict[str, Any]] = []
    baseline_match_rate: float
    baseline_source: str = "dry_run_subset"
    baseline_computed_at: datetime
    baseline_constants_version: str


class MatchedRecord(BaseModel):
    """Pairing result between a left ledger record and right statement record."""
    l_rid: int
    r_rid: int
    composite_score: float
    components: Dict[str, float]
    policy_version: str


class UnmatchedRecord(BaseModel):
    """Unpaired record with classified discrepancy reason and diagnostic explanation."""
    side: str  # 'L' (ledger) or 'R' (statement/bank)
    rid: int
    ref: Optional[str] = None
    reason: HypothesisCategory = HypothesisCategory.UNCLASSIFIED
    delta: Optional[float] = None
    match_confidence: Optional[float] = None
    explanation: Optional[str] = None


class VarianceMetrics(BaseModel):
    """Aggregated discrepancy and balance variance metrics."""
    abs_sum: float
    pct_avg: float = 0.0
    signed_sum: float
    per_record: List[Dict[str, Any]]


class ExecutionResult(BaseModel):
    """Comprehensive matching engine execution output."""
    matched: List[MatchedRecord]
    unmatched: List[UnmatchedRecord]
    duplicates: List[Dict[str, Any]]
    splits: List[Dict[str, Any]]
    variance: VarianceMetrics


class FinalReport(BaseModel):
    """Final reconciliation report summarizing volumes, matches, exceptions, and costs."""
    match_rate: float
    precision_vs_truth: Optional[float] = None
    recall_vs_truth: Optional[float] = None
    throughput_rows_per_sec: float
    honest_exception_count: int
    auto_resolved_count: int
    escalated_count: int
    unresolved_count: int
    total_gross: float
    total_net: float
    total_fees: float
    matched_value: float
    exception_value: float
    cost_usd: float
    cost_estimated: bool = False
    elapsed_seconds: float
    llm_user_disagreements: List[Dict[str, Any]] = []
    fallback_events: List[str] = []
    constants_version: str
    retention_note: str
    storage_backend: str = "local_hash_chain"

