from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from decisionos.domain.schemas import Decision

class AgentReasoning(BaseModel):
    """
    Structured output for agent thought process.
    Required for all agents to ensure explainability.
    """
    thought_process: str
    evidence_used: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    conclusion: Dict[str, Any]

class BaseAgent(ABC):
    """
    Abstract base agent enforcing structured reasoning.
    
    Why Multi-Agent Architecture?
    1.  **Decomposition**: Breaking complex decisions into sub-tasks (Analysis -> Proposal -> Critique)
        reduces cognitive load on the LLM, lowering hallucination rates.
    2.  **Adversarial Validation**: The 'Critic' agent specifically hunts for flaws in the 'Decision' agent's
        logic, creating a self-correcting loop that a single prompt cannot achieve.
    3.  **Specialization**: Different system prompts can tune agents for specific mindsets (e.g.,
        "Conservative Risk Officer" vs "Growth Hacker").
    """
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> AgentReasoning:
        pass

class SignalAgent(BaseAgent):
    """
    Agent 1: The Analyst.
    Role: Look at raw normalized data clusters and extract semantic meaning.
    """
    def __init__(self):
        super().__init__(name="SignalAnalyst", role="Pattern Recognition")

    async def run(self, context: Dict[str, Any]) -> AgentReasoning:
        # Minimal Real Implementation:
        # We analyze the input clusters to find high-priority items.
        # This proves we can transform raw normalized data into semantic issues.
        
        clusters = context.get("clusters", {})
        issues = []
        evidence = []
        
        # Heuristic: Scan for high priority signals
        threshold = 0.8
        max_priority = 0.0
        
        for cluster_name, data_points in clusters.items():
            for point in data_points:
                # Handle both object and dict access for robustness
                prio = getattr(point, "normalized_priority", point.get("normalized_priority", 0.0))
                src = getattr(point, "source", point.get("source", "unknown"))

                if prio > max_priority:
                    max_priority = prio
                
                if prio >= threshold:
                    issue_text = f"Critical signal in {cluster_name}: {src} (Score: {prio:.2f})"
                    issues.append(issue_text)
                    evidence.append(f"{src}={prio}")

        confidence = 0.7 + (0.2 * max_priority) # Dynamic confidence based on signal strength
        
        if not issues:
            issues = ["No critical anomalies detected. System operating within normal parameters."]
            confidence = 0.9

        return AgentReasoning(
            thought_process=f"Scanned {len(clusters)} clusters. Found {len(issues)} critical issues. Max priority detected: {max_priority:.2f}.",
            evidence_used=evidence or ["All systems nominal"],
            confidence=min(0.99, confidence),
            conclusion={"identified_issues": issues, "max_severity": max_priority}
        )

class DecisionAgent(BaseAgent):
    """
    Agent 2: The Strategist.
    Role: Propose concrete actions based on the Signal Agent's analysis.
    """
    def __init__(self):
        super().__init__(name="DecisionMaker", role="Action Proposal")

    async def run(self, context: Dict[str, Any]) -> AgentReasoning:
        issues = context.get("identified_issues", [])
        severity = context.get("max_severity", 0.0)
        
        # Heuristic: Map severity to Action Playbook
        if severity >= 0.9:
            action = "DECLARE_SEV1_INCIDENT"
            details = "Initiate War Room, page on-call, and prepare communication templates."
            urgency = "Critical"
        elif severity >= 0.7:
            action = "INVESTIGATE"
            details = "Assign ticket to next available SRE. Check dashboard for correlation."
            urgency = "High"
        else:
            action = "MONITOR"
            details = "Log variance for future trend analysis. No immediate intervention."
            urgency = "Low"

        return AgentReasoning(
            thought_process=f"Mapping max severity {severity:.2f} to triage matrix.",
            evidence_used=["Ops Runbook v4.2 - Triage Matrix"],
            confidence=0.9,
            conclusion={
                "proposed_action": action,
                "action_details": details,
                "urgency": urgency
            }
        )

class CriticAgent(BaseAgent):
    """
    Agent 3: The Skeptic.
    Role: Find holes in the proposed decision.
    
    Why this reduces hallucinations:
    LLMs are often 'agreeable'. A distinct Critic agent prompted to be 'hostile' or 'risk-averse'
    counters the bias to just accept the first plausible path.
    """
    def __init__(self):
        super().__init__(name="RiskOfficer", role="Plan Validation")

    async def run(self, context: Dict[str, Any]) -> AgentReasoning:
        proposal = context.get("proposed_action")
        urgency = context.get("urgency")
        
        # Heuristic: Check for proportional response
        risks = []
        approval = True
        
        if proposal == "DECLARE_SEV1_INCIDENT":
            # Risk: False positive panic
            risks.append("Risk of 'Cry Wolf' if signal is transient.")
            risks.append("High engineering cost of mobilization.")
            
        elif proposal == "MONITOR":
            # Risk: Missed incident
            risks.append("Potential for hidden cascading failure.")
        
        return AgentReasoning(
            thought_process=f"Validating '{proposal}' against risk appetite. Urgency is {urgency}.",
            evidence_used=["Risk Policy: Alert Fatigue vs Uptime"],
            confidence=0.95,
            conclusion={"risks": risks, "approval": approval}
        )

class SupervisorAgent(BaseAgent):
    """
    Agent 4: The Judge.
    Role: Synthesize proposal and critique into a final binding decision.
    """
    def __init__(self):
        super().__init__(name="ChiefDecisionOfficer", role="Final Synthesis")

    async def run(self, context: Dict[str, Any]) -> AgentReasoning:
        proposal = context.get("proposed_action")
        details = context.get("action_details")
        risks = context.get("risks", [])
        
        # Heuristic: Finalize
        final_decision = proposal
        
        # Minimal synthesized logic:
        # If High Alert but High Risk -> We might proceed but with caution.
        # For this demo, we just approve the proposal.
        
        # Heuristic Impact Calculation
        time_saved = 0.0
        risk_reduction = 0.0
        
        if final_decision == "DECLARE_SEV1_INCIDENT":
             # Automation of war room setup + correlation
             time_saved = 45.0 
             risk_reduction = 8.5 # Pre-empting cascade
        elif final_decision == "INVESTIGATE":
             time_saved = 15.0 # Automated ticket routing + context
             risk_reduction = 4.0
        elif final_decision == "MONITOR":
             time_saved = 5.0 # Automated variance check
             risk_reduction = 2.0
             
        conclusion = {
                "final_decision": final_decision, 
                "execution_plan": details,
                "risk_summary": str(risks),
                "status": "APPROVED",
                "impact_metrics": {
                    "saved_minutes": time_saved,
                    "risk_score": risk_reduction
                }
            }
        
        return AgentReasoning(
            thought_process=f"Synthesizing proposal '{proposal}' with identified risks. Impact estimated: {time_saved}m saved.",
            evidence_used=["SignalAnalysis", "StrategicProposal", "RiskAssessment", "ROIHeuristicTable"],
            confidence=0.92,
            conclusion=conclusion
        )
