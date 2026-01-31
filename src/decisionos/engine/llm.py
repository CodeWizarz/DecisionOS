import json
import httpx
import structlog
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel

from decisionos.core.config import settings

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

class LLMInferenceAdapter:
    """
    Adapter for performing optional LLM inference.
    
    Design Philosophy:
    1.  **Optionality**: This system is designed to run deterministically without LLMs by default.
        LLM usage is a value-add optimization, not a critical path dependency.
    2.  **Kill-Switches**: Enterprise deployments often require the ability to instantly sever 
        external API connections (for compliance, cost control, or outage mitigation) without 
        bringing down the application. The `USE_LLM` flag serves as this hard kill-switch.
    3.  **Cost/Latency Trade-offs**: LLM calls introduce significant latency (500ms-3s) and cost 
        ($0.01-$0.10 per call) compared to local heuristics (<1ms, $0). 
        The adapter structure allows us to easily swap models or fallback to smaller models.
    """
    
    def __init__(self):
        self.enabled = settings.USE_LLM
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL
        
        if self.enabled and not self.api_key:
            logger.warning("llm_enabled_but_no_key_found", 
                           msg="USE_LLM is True but LLM_API_KEY is missing. Disabling LLM.")
            self.enabled = False

    async def predict(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        output_schema: Type[T],
        temperature: float = 0.0
    ) -> Optional[T]:
        """
        Execute an LLM inference call and parse the result into the provided Pydantic schema.
        
        Returns None if LLMs are disabled or the call fails (graceful degradation).
        """
        if not self.enabled:
            return None

        logger.info("llm_inference_start", model=self.model)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Force JSON mode for structured output reliability
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        # Append schema instruction to system prompt to ensure JSON adherence
        # Most modern models need explicit schema in prompt even with json_mode
        payload["messages"][0]["content"] += f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(output_schema.model_json_schema())}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", 
                    json=payload, 
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error("llm_api_error", status_code=response.status_code, body=response.text)
                    return None
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse and Validate
                parsed_json = json.loads(content)
                result = output_schema.model_validate(parsed_json)
                
                logger.info("llm_inference_success")
                return result

        except Exception as e:
            logger.error("llm_inference_failed", error=str(e))
            return None
