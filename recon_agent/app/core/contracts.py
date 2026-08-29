from datetime import date, datetime
from enum import Enum
from typing import Callable, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class MessageKind(str, Enum):
    CHAT = "chat"
    ARTIFACT = "artifact"
    TRACE = "trace"
    CONTROL = "control"

class ConfidenceScope(str, Enum):
    MAPPING = "mapping"
    MATCH = "match"
    EXCEPTION = "exception"

class Actor(str, Enum):
    LLM = "llm"
    USER = "user"
    SYSTEM = "system"
    FALLBACK = "fallback"

class EvidencePiece(str, Enum):
    KEY_MATCH = "key_match"
    AMOUNT_WITHIN_TOL = "amount_within_tol"
    DATE_WITHIN_WINDOW = "date_within_window"
    FEE_MODEL_MATCH = "fee_model_match"

class HypothesisCategory(str, Enum):
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

HYPOTHESIS_PRIORITY = {
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
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=2000)

class ArtifactPayload(BaseModel):
    kind: str
    schema_version: str = "1.0"
    rows: Optional[list[dict]] = None
    summary: dict = {}
    confidence_threshold: float
    fallback_events: list[str] = []

class TracePayload(BaseModel):
    event: str
    detail: dict = {}

class ControlPayload(BaseModel):
    event: str
    state: Optional[str] = None
    abort_token: Optional[str] = None
    detail: dict = {}

SCHEMAS = {
    MessageKind.CHAT: ChatPayload,
    MessageKind.ARTIFACT: ArtifactPayload,
    MessageKind.TRACE: TracePayload,
    MessageKind.CONTROL: ControlPayload,
}


class ToolCall(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    args_schema: Type[BaseModel]
    result_schema: Type[BaseModel]
    timeout_s: float
    retries: int
    fallback: Callable
    cost_budget_usd: float

class FeeSchedule(BaseModel):
    provider: str
    schedule_id: str
    version: str
    effective_from: date
    effective_until: Optional[date] = None
    model_type: str
    params: dict
    gst_rate: float = 0.0
    currency: str = "INR"

class ConfidenceScore(BaseModel):
    scope: ConfidenceScope
    value: float = Field(ge=0, le=1)
    components: dict[str, float]
    constants_version: str
    constants_loaded_at: datetime

class DecisionRecord(BaseModel):
    decision_id: str
    ts: datetime
    state: str
    actor: Actor
    decision_kind: str
    proposal: dict
    final: dict
    overridden: bool = False
    override_reason: Optional[str] = None
    confidence: float
    evidence: list[EvidencePiece]
    fallback_used: Optional[str] = None

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    numeric_ratio: float
    date_ratio: float
    cardinality: float
    null_rate: float
    min_len: int
    max_len: int
    sample_values: list[str]
    pii_likelihood: float

class PolicyComponent(BaseModel):
    component: MatchComponent
    params: dict
    enabled: bool = True
    precedence: int

class Policy(BaseModel):
    components: list[PolicyComponent]
    generated_from: str = "deterministic_library_v0"
    revision_history: list[dict] = []
    baseline_match_rate: float
    baseline_source: str = "dry_run_subset"
    baseline_computed_at: datetime
    baseline_constants_version: str

class MatchedRecord(BaseModel):
    l_rid: int
    r_rid: int
    composite_score: float
    components: dict[str, float]
    policy_version: str

class UnmatchedRecord(BaseModel):
    side: str
    rid: int
    ref: Optional[str] = None
    reason: HypothesisCategory = HypothesisCategory.UNCLASSIFIED
    delta: Optional[float] = None
    match_confidence: Optional[float] = None
    explanation: Optional[str] = None

class VarianceMetrics(BaseModel):
    abs_sum: float
    pct_avg: float = 0.0
    signed_sum: float
    per_record: list[dict]

class ExecutionResult(BaseModel):
    matched: list[MatchedRecord]
    unmatched: list[UnmatchedRecord]
    duplicates: list[dict]
    splits: list[dict]
    variance: VarianceMetrics

class FinalReport(BaseModel):
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
    llm_user_disagreements: list[dict] = []
    fallback_events: list[str] = []
    constants_version: str
    retention_note: str
    storage_backend: str = "local_hash_chain"
