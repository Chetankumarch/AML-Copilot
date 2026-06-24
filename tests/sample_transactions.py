"""Sample PaySim transactions for manual testing."""

HIGH_RISK_TRANSFER = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 4500000.00,
    "nameOrig": "C1234567890",
    "oldbalanceOrg": 4500000.00,
    "newbalanceOrig": 0.00,
    "nameDest": "C9876543210",
    "oldbalanceDest": 0.00,
    "newbalanceDest": 0.00,
}

LOW_RISK_PAYMENT = {
    "step": 5,
    "type": "PAYMENT",
    "amount": 45.99,
    "nameOrig": "C1111111111",
    "oldbalanceOrg": 12000.00,
    "newbalanceOrig": 11954.01,
    "nameDest": "M2222222222",
    "oldbalanceDest": 50000.00,
    "newbalanceDest": 50045.99,
}

SUSPICIOUS_CASHOUT = {
    "step": 3,
    "type": "CASH_OUT",
    "amount": 350000.00,
    "nameOrig": "C3333333333",
    "oldbalanceOrg": 350000.00,
    "newbalanceOrig": 0.00,
    "nameDest": "C4444444444",
    "oldbalanceDest": 0.00,
    "newbalanceDest": 350000.00,
}
