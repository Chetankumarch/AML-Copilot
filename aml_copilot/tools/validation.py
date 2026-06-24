"""Deterministic SAR draft validation against FinCEN filing requirements."""

_RISK_LEVEL_ACTIONS = {
    "CRITICAL": ["immediate", "file", "filing"],
    "HIGH": ["file", "filing", "review"],
    "MEDIUM": ["monitor", "monitoring", "enhanced"],
    "LOW": ["no further", "dismiss", "no action"],
}

_MIN_SUBSTANTIVE_LENGTH = 20


def validate_sar_draft(
    sar_subject_info: str,
    sar_suspicious_activity: str,
    sar_supporting_evidence: str,
    sar_risk_assessment: str,
    sar_recommended_action: str,
    triage_risk_score: int,
    triage_risk_level: str,
    triage_flags: list[str],
    evidence_sanctions_hits: list[dict],
    evidence_prior_cases: list[dict],
) -> dict:
    """Validate a SAR draft against triage results and evidence data.

    Performs deterministic checks for completeness, consistency, and
    evidence grounding. Returns a validation result with score, findings,
    and verdict.

    Args:
        sar_subject_info: Subject identification section of the SAR draft.
        sar_suspicious_activity: Activity description section.
        sar_supporting_evidence: Supporting evidence section.
        sar_risk_assessment: Risk assessment section.
        sar_recommended_action: Recommended action section.
        triage_risk_score: Risk score from triage (0-100).
        triage_risk_level: Risk level from triage (CRITICAL/HIGH/MEDIUM/LOW).
        triage_flags: List of triggered risk flags from triage.
        evidence_sanctions_hits: List of sanctions match dicts from evidence.
        evidence_prior_cases: List of prior case dicts from evidence.

    Returns:
        A dict with verdict, completeness_score, missing_elements,
        unsupported_claims, and revision_instructions.
    """
    missing_elements = []
    unsupported_claims = []
    section_scores = {}

    sections = {
        "subject_info": sar_subject_info,
        "suspicious_activity": sar_suspicious_activity,
        "supporting_evidence": sar_supporting_evidence,
        "risk_assessment": sar_risk_assessment,
        "recommended_action": sar_recommended_action,
    }
    for name, text in sections.items():
        if not text or len(text.strip()) < _MIN_SUBSTANTIVE_LENGTH:
            missing_elements.append(f"{name}: section is missing or too short (under {_MIN_SUBSTANTIVE_LENGTH} chars)")
            section_scores[name] = 0
        else:
            section_scores[name] = 20

    risk_assessment_lower = sar_risk_assessment.lower() if sar_risk_assessment else ""
    if str(triage_risk_score) not in risk_assessment_lower and not _number_mentioned(risk_assessment_lower, triage_risk_score):
        missing_elements.append(f"risk_assessment: does not mention the risk score ({triage_risk_score})")
        section_scores["risk_assessment"] = max(section_scores.get("risk_assessment", 0) - 5, 0)

    if triage_risk_level and triage_risk_level.lower() not in risk_assessment_lower:
        missing_elements.append(f"risk_assessment: does not mention the risk level ({triage_risk_level})")
        section_scores["risk_assessment"] = max(section_scores.get("risk_assessment", 0) - 5, 0)

    action_lower = sar_recommended_action.lower() if sar_recommended_action else ""
    expected_keywords = _RISK_LEVEL_ACTIONS.get(triage_risk_level, [])
    if expected_keywords and not any(kw in action_lower for kw in expected_keywords):
        missing_elements.append(
            f"recommended_action: action does not match risk level {triage_risk_level} "
            f"(expected keywords: {', '.join(expected_keywords)})"
        )
        section_scores["recommended_action"] = max(section_scores.get("recommended_action", 0) - 10, 0)

    activity_lower = sar_suspicious_activity.lower() if sar_suspicious_activity else ""
    flags_referenced = 0
    for flag in triage_flags:
        flag_keywords = _extract_flag_keywords(flag)
        if any(kw in activity_lower for kw in flag_keywords):
            flags_referenced += 1
    if triage_flags and flags_referenced == 0:
        missing_elements.append("suspicious_activity: does not reference any triage risk flags")
        section_scores["suspicious_activity"] = max(section_scores.get("suspicious_activity", 0) - 10, 0)

    evidence_lower = sar_supporting_evidence.lower() if sar_supporting_evidence else ""

    for hit in evidence_sanctions_hits:
        list_name = hit.get("sanctions_list", "")
        entity = hit.get("entity_name", "")
        if list_name and list_name.lower() not in evidence_lower and entity.lower() not in evidence_lower:
            missing_elements.append(
                f"supporting_evidence: sanctions match on {list_name} ({entity}) not cited"
            )
            section_scores["supporting_evidence"] = max(section_scores.get("supporting_evidence", 0) - 5, 0)

    for case in evidence_prior_cases:
        case_id = case.get("case_id", "")
        if case_id and case_id.lower() not in evidence_lower:
            missing_elements.append(
                f"supporting_evidence: prior case {case_id} not cited"
            )
            section_scores["supporting_evidence"] = max(section_scores.get("supporting_evidence", 0) - 5, 0)

    sanctions_keywords = ["sanction", "ofac", "sdn", "un-sc"]
    mentions_sanctions = any(kw in evidence_lower for kw in sanctions_keywords)
    if mentions_sanctions and not evidence_sanctions_hits:
        unsupported_claims.append("supporting_evidence: references sanctions but no sanctions hits in evidence")

    case_keywords = ["sar-", "case", "filed", "prior"]
    mentions_cases = any(kw in evidence_lower for kw in case_keywords)
    if mentions_cases and not evidence_prior_cases:
        unsupported_claims.append("supporting_evidence: references prior cases but none found in evidence")

    completeness_score = max(0, min(100, sum(section_scores.values())))

    has_missing = len(missing_elements) > 0
    has_unsupported = len(unsupported_claims) > 0
    verdict = "FAIL" if has_missing or has_unsupported else "PASS"

    revision_instructions = ""
    if verdict == "FAIL":
        parts = []
        if has_missing:
            parts.append(f"Address {len(missing_elements)} missing/incomplete element(s).")
        if has_unsupported:
            parts.append(f"Remove or substantiate {len(unsupported_claims)} unsupported claim(s).")
        revision_instructions = " ".join(parts)

    return {
        "verdict": verdict,
        "completeness_score": completeness_score,
        "missing_elements": missing_elements,
        "unsupported_claims": unsupported_claims,
        "revision_instructions": revision_instructions,
    }


def _number_mentioned(text: str, number: int) -> bool:
    return str(number) in text


def _extract_flag_keywords(flag: str) -> list[str]:
    keywords = []
    flag_lower = flag.lower()
    if "large" in flag_lower and "transfer" in flag_lower:
        keywords.extend(["large transfer", "transfer"])
    if "large" in flag_lower and "cash_out" in flag_lower:
        keywords.extend(["large cash_out", "cash_out", "cash out"])
    if "balance drain" in flag_lower:
        keywords.extend(["balance drain", "drain", "zero"])
    if "empty destination" in flag_lower:
        keywords.extend(["empty destination", "zero-balance", "zero balance"])
    if "overdraft" in flag_lower:
        keywords.extend(["overdraft", "exceeds"])
    if "round" in flag_lower:
        keywords.extend(["round", "round-number", "round number"])
    if not keywords:
        words = [w for w in flag_lower.split() if len(w) > 3]
        keywords = words[:3]
    return keywords
