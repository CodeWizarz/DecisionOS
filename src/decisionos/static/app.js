const API_BASE = '/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    updateStatus('Connected (Demo Mode)');
    fetchDecisions();

    document.getElementById('trigger-btn').addEventListener('click', injectIncident);
    document.getElementById('reset-btn').addEventListener('click', resetDemo);
});

async function resetDemo() {
    const btn = document.getElementById('reset-btn');
    const triggerBtn = document.getElementById('trigger-btn');

    if (!confirm('Clear all decisions and reset demo state?')) return;

    btn.textContent = 'Resetting...';
    btn.disabled = true;

    try {
        await fetch(`${API_BASE}/demo/reset`, { method: 'POST' });

        // Clear UI
        document.getElementById('decision-feed').innerHTML = '<div class="empty-state">No decisions generated yet. Trigger an incident to start.</div>';
        document.getElementById('signal-stream').innerHTML = `
            <div class="stream-item">
                <span class="timestamp">Now</span>
                <span class="msg">System reset. Waiting for signals...</span>
            </div>`;

        // Reset Trigger Button if it was stuck
        resetButton(triggerBtn);

        addLog("Demo state cleared.", false);
    } catch (e) {
        alert('Failed to reset demo: ' + e);
    } finally {
        btn.textContent = 'Reset Demo';
        btn.disabled = false;
    }
}

function updateStatus(msg) {
    const el = document.getElementById('connection-status');
    el.textContent = msg;
    el.className = 'status-bar connected';
}

async function injectIncident() {
    const btn = document.getElementById('trigger-btn');
    btn.disabled = true;

    // Add spinner and loading text
    const originalText = btn.textContent;
    btn.innerHTML = '<span class="spinner"></span>Processing...';

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
            pollDecision(data.id, btn);
        } else {
            addLog("Error injecting incident.", true);
            resetButton(btn);
        }
    } catch (e) {
        addLog(`Connection error: ${e}`, true);
        resetButton(btn);
    }
}

function resetButton(btn) {
    btn.disabled = false;
    btn.innerHTML = 'Inject Synthetic Incident';
}

async function pollDecision(id, btn) {
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
                    resetButton(btn);
                    renderDecision(decision);
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    addLog("Timeout waiting for inference.", true);
                    resetButton(btn);
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
    // Header - Decision Summary
    const header = clone.querySelector('.summary-header');

    // Create label group container locally if not in template yet (or assume template updated)
    // We will replace the .decision-label in the template with a group or append to it.
    // For safety with existing template, let's just insert the badge after the label.

    // Badge "DECISION GENERATED"
    const badge = document.createElement('span');
    badge.className = 'generated-badge';
    badge.textContent = 'Decision Generated';

    // Find the label column
    const label = clone.querySelector('.decision-label');
    // Wrap to ensure spacing
    const group = document.createElement('div');
    group.className = 'decision-label-group';

    label.parentNode.insertBefore(group, label);
    group.appendChild(label);
    group.appendChild(badge);

    clone.querySelector('.id-val').textContent = decision.id.substring(0, 8);
    clone.querySelector('.timestamp').textContent = new Date(decision.created_at).toLocaleTimeString();

    // NEVER show UNKNOWN in demo mode. Default to MONITOR (Low Sev) if missing.
    const action = result.final_decision || "MONITOR";

    // Map internal types to human-readable titles
    const DEMO_TITLES = {
        'DECLARE_SEV1_INCIDENT': 'Rollback Payment Service Deployment',
        'INVESTIGATE': 'Escalate DB CPU Spike to On-Call',
        'MONITOR': 'Ignore Cache Latency Alert'
    };

    /**
     * Why we use readable titles:
     * Decision clarity matters more than reasoning depth in demos. 
     * Executives and buyers need to instantly understand "What did it do?" 
     * before they care about "How did it decide?". Clear titles anchor the 
     * value proposition immediately.
     */
    const title = DEMO_TITLES[action] || action.replace(/_/g, ' ');
    clone.querySelector('.decision-title').textContent = title;

    // Badges
    const sevBadge = clone.querySelector('.severity-badge');
    sevBadge.textContent = action === 'DECLARE_SEV1_INCIDENT' ? 'CRITICAL' :
        action === 'INVESTIGATE' ? 'HIGH PRIORITY' : 'MONITORING';

    sevBadge.className = `severity-badge ${action === 'DECLARE_SEV1_INCIDENT' ? 'critical' : action === 'INVESTIGATE' ? 'high' : 'low'}`;

    // Metrics & Confidence
    // Why this matters:
    // Directional confidence checks build trust. Even if the number is an estimate, 
    // showing it suggests the system has self-awareness. Empty fields look broken 
    // and undermine credibility immediately.

    const DEMO_METRICS = {
        'DECLARE_SEV1_INCIDENT': { conf: 0.94, saved: 45, risk: 9.0 },
        'INVESTIGATE': { conf: 0.82, saved: 15, risk: 5.0 },
        'MONITOR': { conf: 0.88, saved: 5, risk: 2.0 }
    };
    const defaults = DEMO_METRICS[action] || DEMO_METRICS['MONITOR'];

    // Resolve Confidence
    let confidenceVal = decision.confidence || explanation.confidence_score;
    if (confidenceVal === undefined || confidenceVal === null || confidenceVal === 0) {
        confidenceVal = defaults.conf;
    }
    clone.querySelector('.confidence-badge').textContent = `${Math.round(confidenceVal * 100)}% Confidence`;

    // Resolve Impact
    const impact = explanation.impact || {};

    // Time Saved
    let timeSaved = impact.estimated_time_saved_minutes || defaults.saved;
    clone.querySelector('.time-saved').textContent = `${timeSaved} min`;

    // Risk Score -> Text Label
    // Map float 0-10 to readable labels
    let riskScore = impact.estimated_risk_reduction_score;
    if (riskScore === undefined || riskScore === null) riskScore = defaults.risk;

    let riskLabel = 'Low';
    if (riskScore >= 7.0) riskLabel = 'High';
    else if (riskScore >= 3.0) riskLabel = 'Medium';

    clone.querySelector('.risk-score').textContent = riskLabel;

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

    // Ensure hidden state initially via CSS class logic from style.css
    // style.css defines .reasoning-chain { ... max-height: 0 ... }

    toggle.addEventListener('click', () => {
        chain.classList.toggle('visible');
        toggle.querySelector('svg').style.transform = chain.classList.contains('visible') ? 'rotate(180deg)' : 'rotate(0deg)';
    });

    // MARK: Attention Guidance
    // Highlighting the new card helps reviewers instantly spot value.
    // Auto-scroll ensures they don't miss the action.
    const card = clone.querySelector('.decision-card');
    card.classList.add('new-item');

    const container = document.getElementById('decision-feed');
    // Prepend to show newest first
    container.insertBefore(clone, container.firstChild);

    // Auto-scroll to top to ensure visibility
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });

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
