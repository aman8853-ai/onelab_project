from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import math

from backend.data_generator import generate_datasets
from backend.reconciliation import reconcile

app = FastAPI(title="Payment Reconciliation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store our datasets in memory
global_txns = None
global_stls = None
global_results = None

def clean_for_json(obj):
    # Convert numpy types to python native types
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif pd.isna(obj) or (isinstance(obj, float) and math.isnan(obj)):
        return None
    elif hasattr(obj, 'item'): 
        return obj.item()
    else:
        return obj

@app.post("/api/generate-data")
async def api_generate_data(num_records: int = 1000):
    global global_txns, global_stls, global_results
    try:
        global_txns, global_stls = generate_datasets(num_records)
        global_results = None # Reset previous results
        return {
            "message": "Data generated successfully",
            "transactions_count": len(global_txns),
            "settlements_count": len(global_stls)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reconcile")
async def api_reconcile():
    global global_txns, global_stls, global_results
    if global_txns is None or global_stls is None:
        raise HTTPException(status_code=400, detail="No data available. Please generate data first.")
        
    try:
        raw_results = reconcile(global_txns, global_stls)
        global_results = clean_for_json(raw_results)
        return {
            "message": "Reconciliation completed successfully",
            "stats": global_results['stats']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report")
async def api_report():
    global global_results
    if global_results is None:
        raise HTTPException(status_code=400, detail="Reconciliation has not been run yet.")
        
    return {
        "stats": global_results['stats'],
        "anomalies": global_results['anomalies'],
        "sample_matches": global_results['matches'][:10]
    }
