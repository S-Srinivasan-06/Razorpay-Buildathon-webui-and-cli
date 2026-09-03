"""Rule Compiler: Natural Language to Segment Fee/Tax Rules with Ambiguity Detection.

Parses natural language instructions (e.g. 'first 20% have 2% fee, next 80% have 1.5% fee',
'if method is upi fee is 0%, if credit_card fee is 1.8%') into structured FeeTaxRule instances.
Enforces ambiguity checks: if rules leave unhandled gaps or create unprioritized overlaps,
it returns a clarifying question before applying.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from app.core.contracts import FeeTaxRule, SegmentMatcher


class RuleCompilerResult(BaseModel):
    """Result of compiling natural language instructions into segment rules."""
    rules: List[FeeTaxRule] = Field(default_factory=list)
    coverage_pct: float = 100.0
    has_ambiguity: bool = False
    ambiguity_reason: Optional[str] = None
    clarifying_question: Optional[str] = None


def compile_rules_from_text(instruction: str) -> RuleCompilerResult:
    """Compile natural language text into segment rules with ambiguity validation.
    
    Args:
        instruction: Natural language rule instructions.
        
    Returns:
        RuleCompilerResult containing parsed rules or ambiguity questions.
    """
    text = instruction.strip()
    rules: List[FeeTaxRule] = []
    
    # 1. Percentage Range Pattern: e.g. "first 20% rows have 2% fee and 18% gst, the next 80% have 1.5% fee and 18% gst"
    pct_matches = list(re.finditer(
        r"(?:first|next|remaining|last)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:rows|data|transactions)?\s*(?:have|use|with|at)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:fee|charge|mdr)(?:\s*(?:and|\+|,)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:gst|tax))?",
        text,
        re.IGNORECASE,
    ))
    
    if pct_matches:
        # Step 1: Parse all (keyword, slice_pct, fee_val, gst_val) tuples first
        segments = []
        for m in pct_matches:
            # Determine segment anchor keyword to detect "last"/"remaining"
            start_char = max(0, m.start() - 12)
            prefix_text = text[start_char:m.start()].lower()
            is_last_or_remaining = bool(re.search(r"\b(last|remaining)\b", prefix_text))
            
            slice_pct = float(m.group(1))
            fee_val = float(m.group(2)) / 100.0
            gst_val = float(m.group(3)) / 100.0 if m.group(3) else 0.18
            segments.append((slice_pct, fee_val, gst_val, is_last_or_remaining))
        
        # Step 2: Resolve anchored start positions correctly.
        # "last 20%" means (80%, 100%), "first 30%" means (0%, 30%), "next X%" is sequential.
        total_pct = sum(s[0] for s in segments)
        rules = []
        cur_pct = 0.0
        total_covered = 0.0
        
        for idx, (slice_pct, fee_val, gst_val, is_tail) in enumerate(segments, 1):
            if is_tail:
                # Tail-anchored: place at the END of the remaining space
                start_p = round(100.0 - slice_pct, 4)
                end_p = 100.0
            else:
                start_p = cur_pct
                end_p = min(100.0, cur_pct + slice_pct)
                cur_pct = end_p
            total_covered += slice_pct
            
            rule = FeeTaxRule(
                rule_id=f"rule_pct_{idx}_{uuid.uuid4().hex[:4]}",
                label=f"Rows {start_p:.0f}%-{end_p:.0f}% ({fee_val*100:.1f}% Fee + {gst_val*100:.1f}% GST)",
                matcher=SegmentMatcher(
                    kind="row_range_pct",
                    start_pct=start_p,
                    end_pct=end_p,
                ),
                fee_rate=fee_val,
                gst_rate=gst_val,
                priority=idx,
                source="ai_interpreted",
            )
            rules.append(rule)
            
        if total_covered < 99.9:
            return RuleCompilerResult(
                rules=rules,
                coverage_pct=total_covered,
                has_ambiguity=True,
                ambiguity_reason=f"Rules cover only {total_covered:.1f}% of dataset rows.",
                clarifying_question=(
                    f"The specified slices cover {total_covered:.1f}% of transactions (rows {cur_pct:.1f}%-100% are unassigned). "
                    f"What fee and tax rate should apply to the remaining {100 - total_covered:.1f}% of rows?"
                ),
            )
        return RuleCompilerResult(rules=rules, coverage_pct=total_covered, has_ambiguity=False)

    # 2. Column / Method Equality Pattern: e.g. "if method is upi use 0% fee, if credit_card use 1.8% fee"
    col_matches = list(re.finditer(
        r"(?:if|for|when)\s*([a-zA-Z_]+)\s*(?:is|=|equals|in)?\s*['\"]?([a-zA-Z0-9_-]+)['\"]?\s*(?:use|have|at|with)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:fee|charge|mdr|tax|gst)(?:\s*(?:and|\+|,)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:gst|tax))?",
        text,
        re.IGNORECASE,
    ))

    # Also catalog item pattern: e.g. "for electronics tax is 18%, for books tax is 0%"
    cat_matches = list(re.finditer(
        r"(?:for|on)\s*([a-zA-Z0-9_-]+)\s*(?:tax|gst)\s*(?:is|=|at)?\s*(\d+(?:\.\d+)?)\s*%",
        text,
        re.IGNORECASE,
    ))

    if col_matches:
        seen_vals = set()
        for idx, m in enumerate(col_matches, 1):
            col_name = m.group(1).lower()
            val = m.group(2).lower()
            r1 = float(m.group(3)) / 100.0
            r2 = float(m.group(4)) / 100.0 if m.group(4) else 0.18
            
            if val in seen_vals:
                return RuleCompilerResult(
                    rules=rules,
                    has_ambiguity=True,
                    ambiguity_reason=f"Duplicate conflicting condition for value '{val}'.",
                    clarifying_question=f"Value '{val}' on column '{col_name}' has multiple conflicting rate definitions. Which rate should take precedence?",
                )
            seen_vals.add(val)
            
            rule = FeeTaxRule(
                rule_id=f"rule_col_{idx}_{uuid.uuid4().hex[:4]}",
                label=f"{col_name}={val} ({r1*100:.1f}% Fee + {r2*100:.1f}% GST)",
                matcher=SegmentMatcher(
                    kind="column_equals",
                    column=col_name,
                    value=val,
                ),
                fee_rate=r1,
                gst_rate=r2,
                priority=idx,
                source="ai_interpreted",
            )
            rules.append(rule)
        return RuleCompilerResult(rules=rules, coverage_pct=100.0, has_ambiguity=False)

    if cat_matches:
        for idx, m in enumerate(cat_matches, 1):
            category = m.group(1).lower()
            gst_val = float(m.group(2)) / 100.0
            rule = FeeTaxRule(
                rule_id=f"rule_cat_{idx}_{uuid.uuid4().hex[:4]}",
                label=f"Category '{category}' ({gst_val*100:.1f}% GST)",
                matcher=SegmentMatcher(
                    kind="column_equals",
                    column="category",
                    value=category,
                ),
                fee_rate=0.0,
                gst_rate=gst_val,
                priority=idx,
                source="ai_interpreted",
            )
            rules.append(rule)
        return RuleCompilerResult(rules=rules, coverage_pct=100.0, has_ambiguity=False)

    # 3. Simple Flat Global Policy fallback if mentioned
    flat_m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*fee(?:\s*(?:and|\+|,)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:gst|tax))?", text, re.IGNORECASE)
    if flat_m:
        f_rate = float(flat_m.group(1)) / 100.0
        g_rate = float(flat_m.group(2)) / 100.0 if flat_m.group(2) else 0.18
        rule = FeeTaxRule(
            rule_id=f"rule_all_{uuid.uuid4().hex[:4]}",
            label=f"All Transactions ({f_rate*100:.1f}% Fee + {g_rate*100:.1f}% GST)",
            matcher=SegmentMatcher(kind="all"),
            fee_rate=f_rate,
            gst_rate=g_rate,
            priority=1,
            source="ai_interpreted",
        )
        return RuleCompilerResult(rules=[rule], coverage_pct=100.0, has_ambiguity=False)

    return RuleCompilerResult(
        rules=[],
        has_ambiguity=True,
        ambiguity_reason="Unable to extract clear segment conditions from instruction.",
        clarifying_question="Could you please specify the rules by percentage ranges (e.g., 'first 20% have 2% fee, next 80% have 1.5% fee') or columns (e.g., 'for category electronics tax is 18%')?",
    )
