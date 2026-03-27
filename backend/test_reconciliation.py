import pytest
import pandas as pd
from backend.reconciliation import reconcile
from datetime import datetime

def test_exact_match():
    txns = pd.DataFrame([{
        "transaction_id": "T1",
        "amount": 100.0,
        "timestamp": datetime(2023, 10, 1, 10, 0, 0)
    }])
    stls = pd.DataFrame([{
        "settlement_id": "S1",
        "amount": 100.0,
        "settlement_date": "2023-10-01"
    }])
    res = reconcile(txns, stls)
    assert res['stats']['matched_records'] == 1
    assert len(res['anomalies']) == 0

def test_delayed_match():
    txns = pd.DataFrame([{
        "transaction_id": "T1",
        "amount": 100.0,
        "timestamp": datetime(2023, 10, 1, 10, 0, 0)
    }])
    stls = pd.DataFrame([{
        "settlement_id": "S1",
        "amount": 100.0,
        "settlement_date": "2023-10-02"
    }])
    res = reconcile(txns, stls)
    assert res['stats']['matched_records'] == 1
    assert len(res['anomalies']) == 0

def test_cross_month_anomaly():
    txns = pd.DataFrame([{
        "transaction_id": "T1",
        "amount": 100.0,
        "timestamp": datetime(2023, 10, 31, 23, 0, 0)
    }])
    stls = pd.DataFrame([{
        "settlement_id": "S1",
        "amount": 100.0,
        "settlement_date": "2023-11-01"
    }])
    res = reconcile(txns, stls)
    assert res['stats']['matched_records'] == 0
    assert len(res['anomalies']) == 1
    assert res['anomalies'][0]['type'] == "Cross-month Settlement"

def test_rounding_issue():
    txns = pd.DataFrame([{
        "transaction_id": "T1",
        "amount": 100.04,
        "timestamp": datetime(2023, 10, 1, 10, 0, 0)
    }])
    stls = pd.DataFrame([{
        "settlement_id": "S1",
        "amount": 100.0,
        "settlement_date": "2023-10-02"
    }])
    res = reconcile(txns, stls)
    assert res['stats']['matched_records'] == 0
    assert len(res['anomalies']) == 1
    assert res['anomalies'][0]['type'] == "Rounding Issue"

def test_missing_settlement():
    txns = pd.DataFrame([{
        "transaction_id": "T1",
        "amount": 100.0,
        "timestamp": datetime(2023, 10, 1, 10, 0, 0)
    }])
    stls = pd.DataFrame(columns=["settlement_id", "amount", "settlement_date"])
    res = reconcile(txns, stls)
    assert res['stats']['matched_records'] == 0
    assert len(res['anomalies']) == 1
    assert res['anomalies'][0]['type'] == "Missing Settlement"

def test_missing_transaction():
    txns = pd.DataFrame(columns=["transaction_id", "amount", "timestamp"])
    stls = pd.DataFrame([{
        "settlement_id": "S1",
        "amount": 100.0,
        "settlement_date": "2023-10-01"
    }])
    res = reconcile(txns, stls)
    assert res['stats']['matched_records'] == 0
    assert len(res['anomalies']) == 1
    assert res['anomalies'][0]['type'] == "Missing Transaction"
