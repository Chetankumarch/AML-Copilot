"""Unit tests for the deterministic SAR draft validation tool."""

from aml_copilot.tools.validation import validate_sar_draft


_COMPLETE_DRAFT = {
    "sar_subject_info": "Account C1234567890 initiated a TRANSFER of $4,500,000.00 to account C9876543210.",
    "sar_suspicious_activity": "Large transfer with complete balance drain. The origin account was emptied in a single transaction to an empty destination account.",
    "sar_supporting_evidence": "OFAC-SDN match on origin account: Shell Corp Alpha Ltd. (score 0.92). UN-SC match on destination: Offshore Ventures Group (score 0.87). Prior SAR case SAR-2025-04821 filed 2025-11-15.",
    "sar_risk_assessment": "Risk score 85, risk level CRITICAL. Multiple high-severity indicators combined with sanctions matches.",
    "sar_recommended_action": "Recommend immediate SAR filing given CRITICAL risk level and dual sanctions matches.",
}

_TRIAGE = {
    "triage_risk_score": 85,
    "triage_risk_level": "CRITICAL",
    "triage_flags": [
        "Large TRANSFER: amount 4,500,000.00 exceeds 200,000 threshold",
        "Balance drain: origin account balance dropped to zero",
        "Empty destination: zero-balance account received large transfer",
    ],
}

_EVIDENCE = {
    "evidence_sanctions_hits": [
        {"sanctions_list": "OFAC-SDN", "entity_name": "Shell Corp Alpha Ltd.", "match_score": 0.92},
        {"sanctions_list": "UN-SC", "entity_name": "Offshore Ventures Group", "match_score": 0.87},
    ],
    "evidence_prior_cases": [
        {"case_id": "SAR-2025-04821", "filed_date": "2025-11-15", "outcome": "filed"},
    ],
}


class TestCompleteDraft:
    def test_passes(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert result["verdict"] == "PASS"

    def test_score_is_100(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert result["completeness_score"] == 100

    def test_no_missing_elements(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert result["missing_elements"] == []

    def test_no_unsupported_claims(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert result["unsupported_claims"] == []

    def test_empty_revision_instructions(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert result["revision_instructions"] == ""


class TestMissingSections:
    def test_empty_subject_info(self):
        draft = {**_COMPLETE_DRAFT, "sar_subject_info": ""}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert result["verdict"] == "FAIL"
        assert any("subject_info" in e for e in result["missing_elements"])

    def test_short_section(self):
        draft = {**_COMPLETE_DRAFT, "sar_subject_info": "Too short"}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert result["verdict"] == "FAIL"
        assert any("subject_info" in e for e in result["missing_elements"])

    def test_multiple_missing_sections(self):
        draft = {**_COMPLETE_DRAFT, "sar_subject_info": "", "sar_suspicious_activity": ""}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert result["completeness_score"] <= 60


class TestRiskConsistency:
    def test_missing_risk_score(self):
        draft = {**_COMPLETE_DRAFT, "sar_risk_assessment": "The risk level is CRITICAL based on multiple flags."}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert any("risk score" in e for e in result["missing_elements"])

    def test_missing_risk_level(self):
        draft = {**_COMPLETE_DRAFT, "sar_risk_assessment": "Risk score 85. Multiple indicators triggered."}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert any("risk level" in e for e in result["missing_elements"])

    def test_wrong_action_for_risk_level(self):
        draft = {**_COMPLETE_DRAFT, "sar_recommended_action": "Recommend enhanced monitoring of the account."}
        triage = {**_TRIAGE, "triage_risk_level": "CRITICAL"}
        result = validate_sar_draft(**draft, **triage, **_EVIDENCE)
        assert any("recommended_action" in e for e in result["missing_elements"])


class TestEvidenceGrounding:
    def test_uncited_sanctions_hit(self):
        draft = {**_COMPLETE_DRAFT, "sar_supporting_evidence": "No sanctions matches were found. Prior case SAR-2025-04821 filed."}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert any("sanctions" in e.lower() for e in result["missing_elements"])

    def test_uncited_prior_case(self):
        draft = {**_COMPLETE_DRAFT, "sar_supporting_evidence": "OFAC-SDN match: Shell Corp Alpha Ltd. UN-SC match: Offshore Ventures Group."}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert any("SAR-2025-04821" in e for e in result["missing_elements"])

    def test_fabricated_sanctions_claim(self):
        evidence = {**_EVIDENCE, "evidence_sanctions_hits": []}
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **evidence)
        assert any("sanctions" in c.lower() for c in result["unsupported_claims"])

    def test_fabricated_prior_case_claim(self):
        evidence = {**_EVIDENCE, "evidence_prior_cases": []}
        draft = {**_COMPLETE_DRAFT, "sar_supporting_evidence": "Prior SAR case SAR-2025-04821 was previously filed against this account."}
        result = validate_sar_draft(**draft, **_TRIAGE, **evidence)
        assert any("prior cases" in c.lower() for c in result["unsupported_claims"])


class TestNoEvidenceCleanDraft:
    def test_clean_draft_no_sanctions_no_cases(self):
        draft = {
            **_COMPLETE_DRAFT,
            "sar_supporting_evidence": "Transaction history shows multiple large transfers in recent weeks. No additional matches found.",
        }
        evidence = {"evidence_sanctions_hits": [], "evidence_prior_cases": []}
        result = validate_sar_draft(**draft, **_TRIAGE, **evidence)
        assert result["unsupported_claims"] == []


class TestFlagReferences:
    def test_no_flags_referenced(self):
        draft = {**_COMPLETE_DRAFT, "sar_suspicious_activity": "The transaction was flagged for review by the compliance team."}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert any("risk flags" in e for e in result["missing_elements"])

    def test_partial_flag_reference(self):
        draft = {**_COMPLETE_DRAFT, "sar_suspicious_activity": "Large transfer detected that drained the account balance to zero."}
        result = validate_sar_draft(**draft, **_TRIAGE, **_EVIDENCE)
        assert not any("risk flags" in e for e in result["missing_elements"])


class TestReturnStructure:
    def test_has_all_keys(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert "verdict" in result
        assert "completeness_score" in result
        assert "missing_elements" in result
        assert "unsupported_claims" in result
        assert "revision_instructions" in result

    def test_verdict_is_string(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert isinstance(result["verdict"], str)
        assert result["verdict"] in ("PASS", "FAIL")

    def test_score_in_range(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert 0 <= result["completeness_score"] <= 100

    def test_lists_are_lists(self):
        result = validate_sar_draft(**_COMPLETE_DRAFT, **_TRIAGE, **_EVIDENCE)
        assert isinstance(result["missing_elements"], list)
        assert isinstance(result["unsupported_claims"], list)
