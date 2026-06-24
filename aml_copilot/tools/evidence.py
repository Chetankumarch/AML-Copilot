"""Evidence gathering tools — mock implementations for M2."""

import hashlib

# Synthetic transaction history keyed by account prefix hash.
# Provides deterministic but varied results for any account ID.

_TX_TEMPLATES = [
    {"type": "TRANSFER", "amount": 15000.00, "counterparty": "C9990001"},
    {"type": "CASH_OUT", "amount": 48000.00, "counterparty": "C9990002"},
    {"type": "PAYMENT", "amount": 320.50, "counterparty": "M8880001"},
    {"type": "TRANSFER", "amount": 250000.00, "counterparty": "C9990003"},
    {"type": "CASH_IN", "amount": 5000.00, "counterparty": "C9990004"},
    {"type": "CASH_OUT", "amount": 120000.00, "counterparty": "C9990005"},
    {"type": "PAYMENT", "amount": 1200.00, "counterparty": "M8880002"},
    {"type": "TRANSFER", "amount": 75000.00, "counterparty": "C9990006"},
]

_SANCTIONS_ENTRIES = {
    "C1234567890": {
        "list": "OFAC-SDN",
        "name": "Shell Corp Alpha Ltd.",
        "match_score": 0.92,
    },
    "C9876543210": {
        "list": "UN-SC",
        "name": "Offshore Ventures Group",
        "match_score": 0.87,
    },
    "C553264065": {
        "list": "OFAC-SDN",
        "name": "TransGlobal Holdings",
        "match_score": 0.78,
    },
}

_PRIOR_CASES = {
    "C1234567890": {
        "case_id": "SAR-2025-04821",
        "filed_date": "2025-11-15",
        "outcome": "filed",
        "summary": "Structured transfers totaling $2.3M over 30 days through shell accounts.",
    },
    "C840083671": {
        "case_id": "SAR-2025-07233",
        "filed_date": "2026-01-22",
        "outcome": "under_review",
        "summary": "Rapid balance drain across 4 accounts within 2-hour window.",
    },
}


def _account_hash(account_id: str) -> int:
    return int(hashlib.md5(account_id.encode()).hexdigest(), 16)


def lookup_transaction_history(account_id: str) -> dict:
    """Look up recent transaction history for an account.

    Returns the last few transactions associated with the given account ID.
    This is a mock implementation using deterministic synthetic data.

    Args:
        account_id: The account identifier to look up.

    Returns:
        A dict with account_id and a list of recent transactions.
    """
    h = _account_hash(account_id)
    count = (h % 5) + 1
    start = h % len(_TX_TEMPLATES)
    txns = []
    for i in range(count):
        template = _TX_TEMPLATES[(start + i) % len(_TX_TEMPLATES)]
        multiplier = ((h >> (i * 4)) % 10 + 1) / 5.0
        txns.append({
            "step": (h + i * 7) % 720 + 1,
            "type": template["type"],
            "amount": round(template["amount"] * multiplier, 2),
            "counterparty": template["counterparty"],
        })
    return {
        "account_id": account_id,
        "transaction_count": len(txns),
        "transactions": txns,
    }


def check_sanctions_list(account_id: str) -> dict:
    """Screen an account against OFAC/UN sanctions lists.

    Returns any matching sanctions entries for the given account ID.
    This is a mock implementation with a small set of flagged accounts.

    Args:
        account_id: The account identifier to screen.

    Returns:
        A dict with account_id, matched (bool), and match details if found.
    """
    entry = _SANCTIONS_ENTRIES.get(account_id)
    if entry:
        return {
            "account_id": account_id,
            "matched": True,
            "sanctions_list": entry["list"],
            "entity_name": entry["name"],
            "match_score": entry["match_score"],
        }
    return {
        "account_id": account_id,
        "matched": False,
    }


def search_prior_cases(account_id: str) -> dict:
    """Search for previously filed SARs involving an account.

    Returns any prior SAR cases associated with the given account ID.
    This is a mock implementation with a small set of known cases.

    Args:
        account_id: The account identifier to search.

    Returns:
        A dict with account_id, found (bool), and case details if found.
    """
    case = _PRIOR_CASES.get(account_id)
    if case:
        return {
            "account_id": account_id,
            "found": True,
            "case_id": case["case_id"],
            "filed_date": case["filed_date"],
            "outcome": case["outcome"],
            "summary": case["summary"],
        }
    return {
        "account_id": account_id,
        "found": False,
    }


def gather_evidence(nameOrig: str, nameDest: str) -> dict:
    """Gather all evidence for a flagged transaction.

    Runs transaction history lookup, sanctions screening, and prior case
    search for both origin and destination accounts. Returns a consolidated
    evidence bundle.

    Args:
        nameOrig: The origin account identifier.
        nameDest: The destination account identifier.

    Returns:
        A dict with transaction history, sanctions hits, and prior cases
        for both accounts.
    """
    origin_history = lookup_transaction_history(nameOrig)
    dest_history = lookup_transaction_history(nameDest)
    origin_sanctions = check_sanctions_list(nameOrig)
    dest_sanctions = check_sanctions_list(nameDest)
    origin_cases = search_prior_cases(nameOrig)
    dest_cases = search_prior_cases(nameDest)

    sanctions_hits = []
    if origin_sanctions["matched"]:
        sanctions_hits.append(origin_sanctions)
    if dest_sanctions["matched"]:
        sanctions_hits.append(dest_sanctions)

    prior_cases = []
    if origin_cases["found"]:
        prior_cases.append(origin_cases)
    if dest_cases["found"]:
        prior_cases.append(dest_cases)

    return {
        "origin_history": origin_history,
        "destination_history": dest_history,
        "sanctions_hits": sanctions_hits,
        "prior_cases": prior_cases,
    }
