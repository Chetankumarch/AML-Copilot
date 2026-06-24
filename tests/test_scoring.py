"""Unit tests for the deterministic risk scoring tool."""

from aml_copilot.tools.scoring import compute_risk_score
from tests.sample_transactions import (
    HIGH_RISK_TRANSFER,
    LOW_RISK_PAYMENT,
    SUSPICIOUS_CASHOUT,
)


class TestHighRiskTransfer:
    """HIGH_RISK_TRANSFER: 4.5M TRANSFER, balance drain, empty dest, round number."""

    def test_score_is_critical(self):
        result = compute_risk_score(**HIGH_RISK_TRANSFER)
        assert result["risk_level"] == "CRITICAL"

    def test_score_at_least_76(self):
        result = compute_risk_score(**HIGH_RISK_TRANSFER)
        assert result["risk_score"] >= 76

    def test_flags_large_transfer(self):
        result = compute_risk_score(**HIGH_RISK_TRANSFER)
        assert any("Large TRANSFER" in f for f in result["flags"])

    def test_flags_balance_drain(self):
        result = compute_risk_score(**HIGH_RISK_TRANSFER)
        assert any("Balance drain" in f for f in result["flags"])

    def test_flags_empty_destination(self):
        result = compute_risk_score(**HIGH_RISK_TRANSFER)
        assert any("Empty destination" in f for f in result["flags"])


class TestLowRiskPayment:
    """LOW_RISK_PAYMENT: $45.99 PAYMENT, normal balances."""

    def test_score_is_low(self):
        result = compute_risk_score(**LOW_RISK_PAYMENT)
        assert result["risk_level"] == "LOW"

    def test_score_is_zero(self):
        result = compute_risk_score(**LOW_RISK_PAYMENT)
        assert result["risk_score"] == 0

    def test_no_flags(self):
        result = compute_risk_score(**LOW_RISK_PAYMENT)
        assert result["flags"] == []


class TestSuspiciousCashout:
    """SUSPICIOUS_CASHOUT: 350K CASH_OUT, balance drain."""

    def test_score_is_critical(self):
        result = compute_risk_score(**SUSPICIOUS_CASHOUT)
        assert result["risk_level"] == "CRITICAL"

    def test_flags_large_cashout(self):
        result = compute_risk_score(**SUSPICIOUS_CASHOUT)
        assert any("Large CASH_OUT" in f for f in result["flags"])

    def test_flags_balance_drain(self):
        result = compute_risk_score(**SUSPICIOUS_CASHOUT)
        assert any("Balance drain" in f for f in result["flags"])


class TestEdgeCases:
    def test_exact_threshold_amount_not_flagged(self):
        result = compute_risk_score(
            step=1, type="TRANSFER", amount=200_000,
            nameOrig="C1", oldbalanceOrg=500_000, newbalanceOrig=300_000,
            nameDest="C2", oldbalanceDest=100_000, newbalanceDest=300_000,
        )
        assert "Large TRANSFER" not in str(result["flags"])

    def test_just_above_threshold(self):
        result = compute_risk_score(
            step=1, type="TRANSFER", amount=200_001,
            nameOrig="C1", oldbalanceOrg=500_000, newbalanceOrig=299_999,
            nameDest="C2", oldbalanceDest=100_000, newbalanceDest=300_001,
        )
        assert any("Large TRANSFER" in f for f in result["flags"])

    def test_score_capped_at_100(self):
        result = compute_risk_score(
            step=1, type="TRANSFER", amount=1_000_000,
            nameOrig="C1", oldbalanceOrg=500_000, newbalanceOrig=0,
            nameDest="C2", oldbalanceDest=0, newbalanceDest=1_000_000,
        )
        assert result["risk_score"] == 100

    def test_zero_amount_no_flags(self):
        result = compute_risk_score(
            step=1, type="PAYMENT", amount=0,
            nameOrig="C1", oldbalanceOrg=1000, newbalanceOrig=1000,
            nameDest="C2", oldbalanceDest=5000, newbalanceDest=5000,
        )
        assert result["risk_score"] == 0
        assert result["flags"] == []

    def test_payment_type_large_amount_no_type_flag(self):
        result = compute_risk_score(
            step=1, type="PAYMENT", amount=500_000,
            nameOrig="C1", oldbalanceOrg=1_000_000, newbalanceOrig=500_000,
            nameDest="C2", oldbalanceDest=100_000, newbalanceDest=600_000,
        )
        assert not any("Large" in f for f in result["flags"])

    def test_return_structure(self):
        result = compute_risk_score(**LOW_RISK_PAYMENT)
        assert "risk_score" in result
        assert "risk_level" in result
        assert "flags" in result
        assert isinstance(result["risk_score"], int)
        assert isinstance(result["flags"], list)
