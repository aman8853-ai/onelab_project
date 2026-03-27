import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import os

def generate_datasets(num_records=1000):
    np.random.seed(42)
    
    # Base configuration
    start_date = datetime(2023, 10, 1)
    
    transactions = []
    settlements = []
    
    # Generate exact matches
    for _ in range(num_records):
        txn_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        stl_id = f"STL_{uuid.uuid4().hex[:8].upper()}"
        amount = round(np.random.uniform(10.0, 500.0), 2)
        
        # Random timestamp in Oct 2023
        random_days = np.random.randint(0, 30)
        random_seconds = np.random.randint(0, 86400)
        txn_time = start_date + timedelta(days=random_days, seconds=random_seconds)
        
        # Settlement is 1-2 days later
        stl_delay = np.random.randint(1, 3)
        stl_time = txn_time + timedelta(days=stl_delay)
        
        transactions.append({
            "transaction_id": txn_id,
            "amount": amount,
            "timestamp": txn_time
        })
        
        settlements.append({
            "settlement_id": stl_id,
            "amount": amount,
            "settlement_date": stl_time.strftime('%Y-%m-%d') # Format as string
        })
        
    # Edge Case 1: Cross-month settlement
    # Transaction on Oct 31, settlement on Nov 1
    txn_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
    stl_id = f"STL_{uuid.uuid4().hex[:8].upper()}"
    amount = 150.00
    txn_time = datetime(2023, 10, 31, 23, 0, 0)
    stl_time = datetime(2023, 11, 1).strftime('%Y-%m-%d')
    transactions.append({"transaction_id": txn_id, "amount": amount, "timestamp": txn_time})
    settlements.append({"settlement_id": stl_id, "amount": amount, "settlement_date": stl_time})
    
    # Edge Case 2: Rounding differences
    # Txn amount 100.005 vs Stl 100.00
    txn_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
    stl_id = f"STL_{uuid.uuid4().hex[:8].upper()}"
    amount_txn = 100.005
    amount_stl = 100.00
    txn_time = datetime(2023, 10, 15, 12, 0, 0)
    stl_time = (txn_time.date() + timedelta(days=1)).strftime('%Y-%m-%d')
    transactions.append({"transaction_id": txn_id, "amount": amount_txn, "timestamp": txn_time})
    settlements.append({"settlement_id": stl_id, "amount": amount_stl, "settlement_date": stl_time})
    
    # Edge Case 3: Duplicate transactions (same txn happened twice, but only one settlement)
    txn_id_1 = f"TXN_{uuid.uuid4().hex[:8].upper()}"
    txn_id_2 = f"TXN_{uuid.uuid4().hex[:8].upper()}"
    stl_id = f"STL_{uuid.uuid4().hex[:8].upper()}"
    amount = 75.50
    txn_time = datetime(2023, 10, 20, 10, 0, 0)
    stl_time = (txn_time.date() + timedelta(days=1)).strftime('%Y-%m-%d')
    transactions.append({"transaction_id": txn_id_1, "amount": amount, "timestamp": txn_time})
    transactions.append({"transaction_id": txn_id_2, "amount": amount, "timestamp": txn_time}) # Duplicate
    settlements.append({"settlement_id": stl_id, "amount": amount, "settlement_date": stl_time})
    
    # Edge Case 4: Missing transaction (Refund without original txn OR just a settlement without txn)
    stl_id = f"STL_{uuid.uuid4().hex[:8].upper()}"
    amount = -25.00 # Refund
    stl_time = datetime(2023, 10, 25).strftime('%Y-%m-%d')
    settlements.append({"settlement_id": stl_id, "amount": amount, "settlement_date": stl_time})
    
    # Edge Case 5: Missing settlement (Transaction without settlement)
    txn_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
    amount = 250.00
    txn_time = datetime(2023, 10, 28, 14, 0, 0)
    transactions.append({"transaction_id": txn_id, "amount": amount, "timestamp": txn_time})
    
    # Convert to DataFrames
    df_transactions = pd.DataFrame(transactions)
    df_settlements = pd.DataFrame(settlements)
    
    # Shuffle data
    df_transactions = df_transactions.sample(frac=1).reset_index(drop=True)
    df_settlements = df_settlements.sample(frac=1).reset_index(drop=True)
    
    return df_transactions, df_settlements

def save_datasets(df_transactions, df_settlements, data_dir="data"):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    tx_path = os.path.join(data_dir, "transactions.csv")
    st_path = os.path.join(data_dir, "settlements.csv")
    
    df_transactions.to_csv(tx_path, index=False)
    df_settlements.to_csv(st_path, index=False)
    
    return tx_path, st_path

if __name__ == "__main__":
    txns, stls = generate_datasets(50)
    print("Generated Transactions:")
    print(txns.head())
    print("Generated Settlements:")
    print(stls.head())
