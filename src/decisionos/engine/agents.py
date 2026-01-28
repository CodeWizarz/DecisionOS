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
        # TODO: Integrate with actual LLM backend
        # This is a stub to demonstrate the architecture
        return AgentReasoning(
            thought_process="Analyzed 3 clusters. Found correlation between server latency and customer tickets.",
            evidence_used=["cluster_id:123 (latency > 500ms)", "cluster_id:456 (ticket_vol > 20)"],
            confidence=0.85,
            conclusion={"identified_issues": ["Performance Degradation", "Customer Impact"]}
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
        return AgentReasoning(
            thought_process=f"Given issues {issues}, immediate mitigation is required to prevent SLA breach.",
            evidence_used=["SLA Document Section 4.2", "Historical Incident #992"],
            confidence=0.9,
            conclusion={"proposed_action": "Scale up web-tier", "urgency": "High"}
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
        return AgentReasoning(
            thought_process=f"Critiquing proposal: '{proposal}'. Check for side effects.",
            evidence_used=["Budget Constraints", "Database Connection Limits"],
            confidence=0.95,
            conclusion={"risks": ["Database saturation if web-tier scales too fast"], "approval": False}
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
        risks = context.get("risks", [])
        return AgentReasoning(
            thought_process=f"Balancing proposal '{proposal}' against risks {risks}. Modified plan required.",
            evidence_used=["Proposal Agent Output", "Critic Agent Output"],
            confidence=0.88,
            conclusion={
                "final_decision": "Scale up web-tier with connection pooling limits", 
                "status": "APPROVED_WITH_MODIFICATIONS"
            }
        )
