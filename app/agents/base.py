import os
import asyncio
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self):
        """Initializes the Agent with OpenRouter credentials."""
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set in .env")
            
        # Using the free Nemotron model
        self.model_name = "nvidia/nemotron-nano-12b-v2-vl:free"

    async def execute_with_retry(self, func: Callable, max_retries: int = 3, *args, **kwargs) -> Any:
        """Executes a function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"API Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)
