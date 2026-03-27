import pandas as pd
import numpy as np

def preprocess_data(txns: pd.DataFrame, stls: pd.DataFrame):
    txns = txns.copy()
    stls = stls.copy()
    
    # Normalize dates
    txns['txn_date'] = pd.to_datetime(txns['timestamp']).dt.date
    stls['stl_date'] = pd.to_datetime(stls['settlement_date']).dt.date
    
    # Save original amounts for rounding issue detection before rounding
    txns['original_amount'] = txns['amount']
    stls['original_amount'] = stls['amount']
    
    # Round amounts for standard comparison
    txns['amount'] = txns['amount'].round(2)
    stls['amount'] = stls['amount'].round(2)
    
    # Flags tracking
    txns['matched'] = False
    stls['matched'] = False
    txns['match_id'] = None
    stls['match_id'] = None
    
    return txns, stls

def reconcile(txns: pd.DataFrame, stls: pd.DataFrame):
    txns, stls = preprocess_data(txns, stls)
    matches = []
    anomalies = []
    
    # 1. Exact Match (Amount + Date)
    for idx, txn in txns.iterrows():
        if txn['matched']: continue
        
        # Find exact matches
        potential = stls[(~stls['matched']) & 
                         (stls['amount'] == txn['amount']) & 
                         (stls['stl_date'] == txn['txn_date'])]
        
        if not potential.empty:
            stl_idx = potential.index[0]
            txns.at[idx, 'matched'] = True
            stls.at[stl_idx, 'matched'] = True
            txns.at[idx, 'match_id'] = stls.at[stl_idx, 'settlement_id']
            stls.at[stl_idx, 'match_id'] = txn['transaction_id']
            matches.append({
                "transaction_id": txn['transaction_id'],
                "settlement_id": stls.at[stl_idx, 'settlement_id'],
                "amount": txn['amount'],
                "type": "Exact Match",
                "explanation": "Matched exactly on date and amount."
            })
            
    # 2. Delayed Settlement (1-2 days)
    for idx, txn in txns.iterrows():
        if txn['matched']: continue
        
        # Find 1-2 days delay
        days_delay = [1, 2]
        potential = stls[(~stls['matched']) & 
                         (stls['amount'] == txn['amount']) & 
                         (stls['stl_date'].isin([txn['txn_date'] + pd.Timedelta(days=d) for d in days_delay]))]
                         
        if not potential.empty:
            stl_idx = potential.index[0]
            stl_date_val = stls.at[stl_idx, 'stl_date']
            txns.at[idx, 'matched'] = True
            stls.at[stl_idx, 'matched'] = True
            txns.at[idx, 'match_id'] = stls.at[stl_idx, 'settlement_id']
            stls.at[stl_idx, 'match_id'] = txn['transaction_id']
            
            # Check if cross month
            txn_month = txn['txn_date'].month
            stl_month = stl_date_val.month
            
            if txn_month != stl_month:
                anomaly_type = "Cross-month Settlement"
                expl = f"Transaction {txn['transaction_id']} settled in the next month. Delay: {(stl_date_val - txn['txn_date']).days} days."
                anomalies.append({
                    "transaction_id": txn['transaction_id'],
                    "settlement_id": stls.at[stl_idx, 'settlement_id'],
                    "amount_txn": txn['amount'],
                    "amount_stl": stls.at[stl_idx, 'amount'],
                    "type": anomaly_type,
                    "explanation": expl
                })
            else:
                matches.append({
                    "transaction_id": txn['transaction_id'],
                    "settlement_id": stls.at[stl_idx, 'settlement_id'],
                    "amount": txn['amount'],
                    "type": "Delayed Match",
                    "explanation": f"Matched with {(stl_date_val - txn['txn_date']).days} days delay."
                })
                
    # 3. Rounding Issues (Amounts differ by <= 0.05, date within 0-2 days)
    for idx, txn in txns.iterrows():
        if txn['matched']: continue
        
        # Allow small amount diff
        potential = stls[(~stls['matched']) & 
                         ((stls['original_amount'] - txn['original_amount']).abs() <= 0.05) & 
                         (stls['stl_date'] >= txn['txn_date']) & 
                         (stls['stl_date'] <= txn['txn_date'] + pd.Timedelta(days=2))]
                         
        if not potential.empty:
            stl_idx = potential.index[0]
            txns.at[idx, 'matched'] = True
            stls.at[stl_idx, 'matched'] = True
            txns.at[idx, 'match_id'] = stls.at[stl_idx, 'settlement_id']
            stls.at[stl_idx, 'match_id'] = txn['transaction_id']
            
            anomalies.append({
                "transaction_id": txn['transaction_id'],
                "settlement_id": stls.at[stl_idx, 'settlement_id'],
                "amount_txn": txn['original_amount'],
                "amount_stl": stls.at[stl_idx, 'original_amount'],
                "type": "Rounding Issue",
                "explanation": f"Amount mismatch due to rounding: {txn['original_amount']} vs {stls.at[stl_idx, 'original_amount']}."
            })

    # The rest are entirely unmatched. Classify them.
    unmatched_txns = txns[~txns['matched']]
    unmatched_stls = stls[~stls['matched']]
    
    # Find Duplicates in txns
    for idx, txn in unmatched_txns.iterrows():
        # check if there's a matched transaction with the same amount and date
        is_duplicate = txns[(txns['matched']) & (txns['amount'] == txn['amount']) & (txns['txn_date'] == txn['txn_date'])].shape[0] > 0
        if is_duplicate:
            anomalies.append({
                "transaction_id": txn['transaction_id'],
                "settlement_id": None,
                "amount_txn": txn['amount'],
                "amount_stl": None,
                "type": "Duplicate Entry",
                "explanation": f"Transaction {txn['transaction_id']} appears to be a duplicate. A similar transaction was already settled."
            })
        else:
            anomalies.append({
                "transaction_id": txn['transaction_id'],
                "settlement_id": None,
                "amount_txn": txn['amount'],
                "amount_stl": None,
                "type": "Missing Settlement",
                "explanation": f"Transaction {txn['transaction_id']} has no corresponding settlement from the bank."
            })
            
    # Missing transactions (or refunds)
    for idx, stl in unmatched_stls.iterrows():
        if stl['amount'] < 0:
            anomaly_type = "Refund Without Transaction"
            expl = f"Settlement {stl['settlement_id']} is a refund ({stl['amount']}) but no corresponding transaction found."
        else:
            anomaly_type = "Missing Transaction"
            expl = f"Settlement {stl['settlement_id']} exists but no matching transaction was recorded."
            
        anomalies.append({
            "transaction_id": None,
            "settlement_id": stl['settlement_id'],
            "amount_txn": None,
            "amount_stl": stl['amount'],
            "type": anomaly_type,
            "explanation": expl
        })
        
    # Summary stats
    stats = {
        "total_transactions": len(txns),
        "total_settlements": len(stls),
        "matched_records": len(matches),
        "anomalies_detected": len(anomalies),
        "mismatch_percentage": round(len(anomalies) / max(len(txns), len(stls)) * 100, 2) if max(len(txns), len(stls)) > 0 else 0
    }
        
    return {
        "stats": stats,
        "matches": matches,
        "anomalies": anomalies
    }

if __name__ == "__main__":
    from data_generator import generate_datasets
    txns, stls = generate_datasets(50)
    res = reconcile(txns, stls)
    print("Stats:", res['stats'])
    print("Anomalies:", res['anomalies'][:2])
