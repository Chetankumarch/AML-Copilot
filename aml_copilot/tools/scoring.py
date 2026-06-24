"""Deterministic risk scoring for PaySim transactions."""


def compute_risk_score(
    step: int,
    type: str,
    amount: float,
    nameOrig: str,
    oldbalanceOrg: float,
    newbalanceOrig: float,
    nameDest: str,
    oldbalanceDest: float,
    newbalanceDest: float,
) -> dict:
    """Compute a deterministic fraud/AML risk score for a PaySim transaction.

    Evaluates the transaction against a set of rule-based indicators and
    returns a numeric score, risk level, and list of triggered flags.

    Args:
        step: Time step (1 step = 1 hour of simulation).
        type: Transaction type (CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER).
        amount: Transaction amount.
        nameOrig: Origin account identifier.
        oldbalanceOrg: Origin account balance before the transaction.
        newbalanceOrig: Origin account balance after the transaction.
        nameDest: Destination account identifier.
        oldbalanceDest: Destination account balance before the transaction.
        newbalanceDest: Destination account balance after the transaction.

    Returns:
        A dict with risk_score (0-100), risk_level, and triggered flags.
    """
    amount = float(amount)
    oldbalanceOrg = float(oldbalanceOrg)
    newbalanceOrig = float(newbalanceOrig)
    oldbalanceDest = float(oldbalanceDest)
    newbalanceDest = float(newbalanceDest)
    step = int(step)

    score = 0
    flags: list[str] = []

    if type in ("TRANSFER", "CASH_OUT") and amount > 200_000:
        score += 30
        flags.append(f"Large {type}: amount {amount:,.2f} exceeds 200,000 threshold")

    if oldbalanceOrg > 0 and newbalanceOrig == 0:
        score += 25
        flags.append("Balance drain: origin account balance dropped to zero")

    if oldbalanceDest == 0 and amount > 10_000:
        score += 20
        flags.append("Empty destination: zero-balance account received large transfer")

    if amount > oldbalanceOrg:
        score += 15
        flags.append(f"Overdraft pattern: amount {amount:,.2f} exceeds prior balance {oldbalanceOrg:,.2f}")

    if amount >= 10_000 and amount % 10_000 == 0:
        score += 10
        flags.append(f"Round-number amount: {amount:,.2f}")

    score = min(score, 100)

    if score >= 76:
        risk_level = "CRITICAL"
    elif score >= 51:
        risk_level = "HIGH"
    elif score >= 26:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "flags": flags,
    }
