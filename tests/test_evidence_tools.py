"""Unit tests for the evidence gathering tools."""

from aml_copilot.tools.evidence import (
    check_sanctions_list,
    gather_evidence,
    lookup_transaction_history,
    search_prior_cases,
)


class TestLookupTransactionHistory:
    def test_returns_account_id(self):
        result = lookup_transaction_history("C1234567890")
        assert result["account_id"] == "C1234567890"

    def test_returns_transactions_list(self):
        result = lookup_transaction_history("C1234567890")
        assert isinstance(result["transactions"], list)
        assert len(result["transactions"]) > 0

    def test_transaction_count_matches(self):
        result = lookup_transaction_history("C1234567890")
        assert result["transaction_count"] == len(result["transactions"])

    def test_transaction_has_required_fields(self):
        result = lookup_transaction_history("C1234567890")
        tx = result["transactions"][0]
        assert "step" in tx
        assert "type" in tx
        assert "amount" in tx
        assert "counterparty" in tx

    def test_deterministic_results(self):
        r1 = lookup_transaction_history("C1234567890")
        r2 = lookup_transaction_history("C1234567890")
        assert r1 == r2

    def test_different_accounts_get_different_history(self):
        r1 = lookup_transaction_history("C1234567890")
        r2 = lookup_transaction_history("C9876543210")
        assert r1["transactions"] != r2["transactions"]

    def test_transaction_count_between_1_and_5(self):
        for acct in ["C111", "C222", "C333", "C444", "C555"]:
            result = lookup_transaction_history(acct)
            assert 1 <= result["transaction_count"] <= 5

    def test_amounts_are_positive(self):
        result = lookup_transaction_history("C1234567890")
        for tx in result["transactions"]:
            assert tx["amount"] > 0


class TestCheckSanctionsList:
    def test_known_match(self):
        result = check_sanctions_list("C1234567890")
        assert result["matched"] is True
        assert result["sanctions_list"] == "OFAC-SDN"

    def test_known_match_has_entity_name(self):
        result = check_sanctions_list("C1234567890")
        assert "entity_name" in result
        assert len(result["entity_name"]) > 0

    def test_known_match_has_score(self):
        result = check_sanctions_list("C1234567890")
        assert 0 < result["match_score"] <= 1.0

    def test_no_match(self):
        result = check_sanctions_list("C0000000000")
        assert result["matched"] is False
        assert "sanctions_list" not in result

    def test_returns_account_id(self):
        result = check_sanctions_list("C0000000000")
        assert result["account_id"] == "C0000000000"

    def test_un_sanctions_list(self):
        result = check_sanctions_list("C9876543210")
        assert result["matched"] is True
        assert result["sanctions_list"] == "UN-SC"


class TestSearchPriorCases:
    def test_known_case(self):
        result = search_prior_cases("C1234567890")
        assert result["found"] is True
        assert result["case_id"] == "SAR-2025-04821"

    def test_known_case_has_details(self):
        result = search_prior_cases("C1234567890")
        assert "filed_date" in result
        assert "outcome" in result
        assert "summary" in result

    def test_no_prior_case(self):
        result = search_prior_cases("C0000000000")
        assert result["found"] is False
        assert "case_id" not in result

    def test_returns_account_id(self):
        result = search_prior_cases("C0000000000")
        assert result["account_id"] == "C0000000000"

    def test_under_review_case(self):
        result = search_prior_cases("C840083671")
        assert result["found"] is True
        assert result["outcome"] == "under_review"

    def test_filed_case(self):
        result = search_prior_cases("C1234567890")
        assert result["outcome"] == "filed"


class TestGatherEvidence:
    def test_returns_origin_history(self):
        result = gather_evidence("C1234567890", "C9876543210")
        assert "origin_history" in result
        assert result["origin_history"]["account_id"] == "C1234567890"

    def test_returns_destination_history(self):
        result = gather_evidence("C1234567890", "C9876543210")
        assert "destination_history" in result
        assert result["destination_history"]["account_id"] == "C9876543210"

    def test_sanctions_hits_with_known_accounts(self):
        result = gather_evidence("C1234567890", "C9876543210")
        assert len(result["sanctions_hits"]) == 2

    def test_sanctions_hits_with_clean_accounts(self):
        result = gather_evidence("C0000000000", "C1111111111")
        assert len(result["sanctions_hits"]) == 0

    def test_prior_cases_with_known_account(self):
        result = gather_evidence("C1234567890", "C0000000000")
        assert len(result["prior_cases"]) == 1
        assert result["prior_cases"][0]["case_id"] == "SAR-2025-04821"

    def test_prior_cases_with_clean_accounts(self):
        result = gather_evidence("C0000000000", "C1111111111")
        assert len(result["prior_cases"]) == 0

    def test_deterministic(self):
        r1 = gather_evidence("C1234567890", "C9876543210")
        r2 = gather_evidence("C1234567890", "C9876543210")
        assert r1 == r2
