# ReconAI - Payment Reconciliation Web Application

ReconAI is an intelligent, end-to-end payment reconciliation engine that automatically detects and explains mismatches between platform transactions and bank settlements. It handles exact matches, delayed 1-2 day settlements, rounding issues, cross-month boundaries, duplicate entries, and missing transactions/settlements.

## Tech Stack
- **Backend:** Python, FastAPI, Pandas, Pytest
- **Frontend:** HTML5, CSS3 (Custom Premium Glassmorphism UI), Vanilla JavaScript
- **Data:** In-memory Pandas DataFrames (with CSV export capability inside the code)

## Features
- **Synthetic Data Generation:** Instantly generate up to thousands of realistic test cases including complex edge cases.
- **Rules-Based Matching Engine:** Utilizing pandas for lightning-fast vectorized exact matching and rule-based anomaly detection.
- **AI-Style Explanations:** For every anomaly, clear natural-language reasons are generated.
- **Modern Dashboard:** Stunning glassmorphism dashboard complete with instant visual statistics and interactive anomaly grids.

## Setup Instructions

### 1. Requirements
Ensure you have Python 3.10+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Backend API
```bash
uvicorn backend.main:app --reload
```
The FastAPI backend will start on `http://127.0.0.1:8000`. You can check the interactive API docs at `http://127.0.0.1:8000/docs`.

### 4. Open the Frontend Dashboard
Simply open the `frontend/index.html` file in your preferred modern web browser. 

*Note: Since the backend is running locally and has CORS enabled, you can just double click `index.html` or run it through a local static server like `vs code live server`.*

## Example Workflow
1. Start the API using Uvicorn.
2. Open the `index.html` Dashboard.
3. Click **"Generate Synthetic Data"**. The engine will construct completely new mock data with randomized edge-cases.
4. Click **"Run Reconciliation"**. The Python Pandas engine instantly matches data, classifies anomalies, and generates explanations.
5. Review the **Dashboard Cards** and **Identified Anomalies** table to inspect logic!

## Testing
Run the Pytest suite to verify the core Pandas matching logic handles edge cases natively:
```bash
python -m pytest backend/test_reconciliation.py
```
