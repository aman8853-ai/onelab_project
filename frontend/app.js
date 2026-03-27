const API_BASE = "http://127.0.0.1:8000/api";

const btnGenerate = document.getElementById("btnGenerate");
const btnReconcile = document.getElementById("btnReconcile");
const statusMessage = document.getElementById("statusMessage");

// Stats
const statTxnCount = document.getElementById("statTxnCount");
const statStlCount = document.getElementById("statStlCount");
const statMatched = document.getElementById("statMatched");
const statAnomalies = document.getElementById("statAnomalies");
const statMismatchPct = document.getElementById("statMismatchPct");

// Tables
const anomaliesTableBody = document.getElementById("anomaliesTableBody");
const matchesTableBody = document.getElementById("matchesTableBody");

// Tabs
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
        
        btn.classList.add("active");
        document.getElementById(btn.dataset.target).classList.add("active");
    });
});

function showStatus(msg, type="success") {
    statusMessage.textContent = msg;
    statusMessage.style.color = type === "error" ? "var(--danger)" : "var(--success)";
    setTimeout(() => { if (statusMessage.textContent === msg) statusMessage.textContent = "" }, 4000);
}

btnGenerate.addEventListener("click", async () => {
    btnGenerate.disabled = true;
    showStatus("Generating synthetic data...", "success");
    try {
        const res = await fetch(`${API_BASE}/generate-data?num_records=500`, { method: "POST" });
        const data = await res.json();
        
        if (res.ok) {
            statTxnCount.textContent = data.transactions_count;
            statStlCount.textContent = data.settlements_count;
            
            // Reset other stats
            statMatched.textContent = "0";
            statAnomalies.textContent = "0";
            statMismatchPct.textContent = "0%";
            
            anomaliesTableBody.innerHTML = `<tr><td colspan="6" class="empty-state">No anomalies to display</td></tr>`;
            matchesTableBody.innerHTML = `<tr><td colspan="5" class="empty-state">No matches to display</td></tr>`;
            
            btnReconcile.disabled = false;
            showStatus("Data generated successfully!");
        } else {
            showStatus(data.detail || "Error generating data", "error");
            btnGenerate.disabled = false;
        }
    } catch (e) {
        showStatus("Network error connecting to backend", "error");
        btnGenerate.disabled = false;
    }
});

btnReconcile.addEventListener("click", async () => {
    btnReconcile.disabled = true;
    btnGenerate.disabled = true;
    showStatus("Running artificial intelligence reconciliation...", "success");
    try {
        const res = await fetch(`${API_BASE}/reconcile`, { method: "POST" });
        if (res.ok) {
            await fetchReport();
            showStatus("Reconciliation complete!");
        } else {
            const data = await res.json();
            showStatus(data.detail || "Error during reconciliation", "error");
        }
    } catch (e) {
        showStatus("Network error connecting to backend", "error");
    } finally {
        btnReconcile.disabled = false;
        btnGenerate.disabled = false;
    }
});

async function fetchReport() {
    try {
        const res = await fetch(`${API_BASE}/report`);
        const data = await res.json();
        
        // Update stats
        statMatched.textContent = data.stats.matched_records;
        statAnomalies.textContent = data.stats.anomalies_detected;
        statMismatchPct.textContent = data.stats.mismatch_percentage + "%";
        
        // Render Anomalies
        anomaliesTableBody.innerHTML = "";
        if (data.anomalies.length === 0) {
            anomaliesTableBody.innerHTML = `<tr><td colspan="6" class="empty-state">No anomalies found</td></tr>`;
        } else {
            data.anomalies.forEach(a => {
                let badgeClass = "error";
                if (a.type.includes("Rounding") || a.type.includes("Cross")) badgeClass = "warn";
                if (a.type.includes("Missing")) badgeClass = "danger";
                
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><span class="type-badge ${badgeClass}">${a.type}</span></td>
                    <td>${a.transaction_id || "-"}</td>
                    <td>${a.settlement_id || "-"}</td>
                    <td>${a.amount_txn !== null ? `$${a.amount_txn.toFixed(2)}` : "-"}</td>
                    <td>${a.amount_stl !== null ? `$${a.amount_stl.toFixed(2)}` : "-"}</td>
                    <td style="color: var(--text-secondary); font-size: 0.9rem;">${a.explanation}</td>
                `;
                anomaliesTableBody.appendChild(tr);
            });
        }
        
        // Render Matches
        matchesTableBody.innerHTML = "";
        if (data.sample_matches.length === 0) {
            matchesTableBody.innerHTML = `<tr><td colspan="5" class="empty-state">No matches found</td></tr>`;
        } else {
            data.sample_matches.forEach(m => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><span class="type-badge success">${m.type}</span></td>
                    <td>${m.transaction_id}</td>
                    <td>${m.settlement_id}</td>
                    <td>$${m.amount.toFixed(2)}</td>
                    <td style="color: var(--text-secondary); font-size: 0.9rem;">${m.explanation}</td>
                `;
                matchesTableBody.appendChild(tr);
            });
        }
        
    } catch (e) {
        console.error(e);
        showStatus("Error fetching report", "error");
    }
}
