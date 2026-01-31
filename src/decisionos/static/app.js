const API_BASE = '/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    updateStatus('Connected (Demo Mode)');
    fetchDecisions();

    document.getElementById('trigger-btn').addEventListener('click', injectIncident);
});

function updateStatus(msg) {
    const el = document.getElementById('connection-status');
    el.textContent = msg;
    el.className = 'status-bar connected';
}

async function injectIncident() {
    const btn = document.getElementById('trigger-btn');
    btn.disabled = true;
    btn.textContent = 'Injecting...';

    addLog("Injecting synthetic latency spikes in web-tier-04...");

    try {
        // Use deterministic Demo API
        const response = await fetch(`${API_BASE}/demo/run-decision`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Empty payload for demo
        });

        if (response.status === 202) {
            const data = await response.json();
            addLog(`Incident ID ${data.id.substring(0, 8)} queued for processing.`);

            // Poll for result
            pollDecision(data.id);
        } else {
            addLog("Error injecting incident.", true);
            btn.disabled = false;
        }
    } catch (e) {
        addLog(`Connection error: ${e}`, true);
        btn.disabled = false;
    }
}

async function pollDecision(id) {
    let attempts = 0;
    const maxAttempts = 20; // 20 * 1s = 20s timeout

    const interval = setInterval(async () => {
        attempts++;
        try {
            // Use deterministic Demo API retrieval
            const res = await fetch(`${API_BASE}/demo/decision/${id}`);
            if (res.ok) {
                const decision = await res.json();

                if (decision.result && decision.result.status !== 'processing') {
                    clearInterval(interval);
                    addLog(`Processing complete. Decision generated.`);
                    document.getElementById('trigger-btn').disabled = false;
                    document.getElementById('trigger-btn').textContent = 'Inject Synthetic Incident';
                    renderDecision(decision);
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    addLog("Timeout waiting for inference.", true);
                    document.getElementById('trigger-btn').disabled = false;
                }
            }
        } catch (e) {
            console.error(e);
        }
    }, 1000);
}

async function fetchDecisions() {
    // We maintain general decision listing for now, but UI primarily drives demo flow
    try {
        const res = await fetch(`${API_BASE}/decisions?limit=5`);
        if (res.ok) {
            const decisions = await res.json();
            const container = document.getElementById('decision-feed');
            container.innerHTML = '';

            if (decisions.length === 0) {
                container.innerHTML = '<div class="empty-state">No decisions generated yet. Trigger an incident to start.</div>';
            } else {
                decisions.forEach(renderDecision);
            }
        }
    } catch (e) {
        console.error("Failed to fetch decisions", e);
    }
}

function renderDecision(decision) {
    const template = document.getElementById('decision-template');
    const clone = template.content.cloneNode(true);

    // Safety check for pending decisions that made it into the list
    if (!decision.result || decision.result.status === 'processing') return;

    const result = decision.result;
    const explanation = decision.explanation || {};

    // Header
    clone.querySelector('.id-val').textContent = decision.id.substring(0, 8);
    clone.querySelector('.timestamp').textContent = new Date(decision.created_at).toLocaleTimeString();

    const action = result.final_decision || "UNKNOWN";
    clone.querySelector('.decision-title').textContent = action.replace(/_/g, ' ');

    // Badges
    const sevBadge = clone.querySelector('.severity-badge');
    sevBadge.textContent = action === 'DECLARE_SEV1_INCIDENT' ? 'CRITICAL' :
        action === 'INVESTIGATE' ? 'HIGH PRIORITY' : 'MONITORING';

    sevBadge.className = `severity-badge ${action === 'DECLARE_SEV1_INCIDENT' ? 'critical' : action === 'INVESTIGATE' ? 'high' : 'low'}`;

    clone.querySelector('.confidence-badge').textContent = `${Math.round(decision.confidence * 100)}% Confidence`;

    // Impact
    const impact = explanation.impact || {};
    clone.querySelector('.time-saved').textContent = impact.estimated_time_saved_minutes ? `${impact.estimated_time_saved_minutes}m` : '-';
    clone.querySelector('.risk-score').textContent = impact.estimated_risk_reduction_score || '-';

    // Agent Chain
    if (explanation.reasoning_trace) {
        explanation.reasoning_trace.forEach(trace => {
            let selector = '';
            if (trace.agent.includes('Signal')) selector = '.signal-step .thought';
            if (trace.agent.includes('Decision')) selector = '.decision-step .thought';
            if (trace.agent.includes('Critic')) selector = '.critic-step .thought';
            if (trace.agent.includes('Supervisor')) selector = '.supervisor-step .thought';

            if (selector) {
                clone.querySelector(selector).textContent = trace.thought;
            }
        });
    }

    // Toggle
    const toggle = clone.querySelector('.expand-toggle');
    const chain = clone.querySelector('.reasoning-chain');
    toggle.addEventListener('click', () => {
        chain.classList.toggle('hidden');
        toggle.querySelector('svg').style.transform = chain.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
    });

    const container = document.getElementById('decision-feed');
    // Prepend to show newest first
    container.insertBefore(clone, container.firstChild);

    // Remove empty state if present
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();
}

function addLog(msg, isError = false) {
    const stream = document.getElementById('signal-stream');
    const div = document.createElement('div');
    div.className = 'stream-item';
    div.innerHTML = `<span class="timestamp">${new Date().toLocaleTimeString()}</span> <span class="msg" style="${isError ? 'color:#ca3b3b' : ''}">${msg}</span>`;
    stream.prepend(div);
}
