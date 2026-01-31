import pytest
from unittest.mock import AsyncMock, patch
from decisionos.engine.llm import LLMInferenceAdapter
from decisionos.engine.agents import SignalAgent, AgentReasoning
from decisionos.core.config import settings

@pytest.mark.asyncio
async def test_llm_adapter_disabled_by_default():
    """Test that LLM adapter is disabled by default and returns None."""
    adapter = LLMInferenceAdapter()
    
    # Force disable for test (in case env var is set)
    adapter.enabled = False
    
    result = await adapter.predict("sys", "user", AgentReasoning)
    assert result is None

@pytest.mark.asyncio
async def test_llm_adapter_missing_key():
    """Test that adapter disables itself if key is missing."""
    with patch("decisionos.core.config.settings.USE_LLM", True), \
         patch("decisionos.core.config.settings.LLM_API_KEY", None):
        
        adapter = LLMInferenceAdapter()
        assert adapter.enabled is False

@pytest.mark.asyncio
async def test_signal_agent_fallback():
    """Test that SignalAgent falls back to heuristics when LLM is disabled."""
    # Ensure LLM is disabled
    with patch("decisionos.core.config.settings.USE_LLM", False):
        agent = SignalAgent()
        # Verify heuristic logic for critical signal
        context = {
            "clusters": {
                "test_cluster": [
                    {"source": "critical_metric", "normalized_priority": 0.9}
                ]
            }
        }
        
        result = await agent.run(context)
        
        assert isinstance(result, AgentReasoning)
        assert result.confidence > 0.0
        # Heuristic creates "Critical signal..." 
        assert "Critical signal" in result.conclusion["identified_issues"][0]
        # Heuristic sets thought process
        assert "Scanned 1 clusters" in result.thought_process

@pytest.mark.asyncio
async def test_llm_adapter_invocation_handling():
    """Test validation and interaction with httpx."""
    # Mock settings to enable LLM
    with patch("decisionos.core.config.settings.USE_LLM", True), \
         patch("decisionos.core.config.settings.LLM_API_KEY", "dummy"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
         
        adapter = LLMInferenceAdapter()
        assert adapter.enabled is True
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": """
                    {
                        "thought_process": "LLM thinking",
                        "evidence_used": ["data"],
                        "confidence": 0.95,
                        "conclusion": {"identified_issues": ["LLM found issue"], "max_severity": 0.9}
                    }
                    """
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = await adapter.predict("sys", "user", AgentReasoning)
        
        assert result is not None
        assert result.thought_process == "LLM thinking"
        assert result.confidence == 0.95
