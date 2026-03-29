"""
HuggingFace Free Inference Extractor - Free Cloud LLM

Uses HuggingFace Inference API (free tier) for stock analysis.
No local GPU required - runs on HuggingFace servers.

Free Tier Limits:
- 30 requests per hour
- 10,000 tokens per month
- Queue-based (may have wait times)

Setup:
1. Get free API key: https://huggingface.co/settings/tokens
2. Add to .env: HUGGINGFACE_API_KEY=your_key_here
"""

import asyncio
from typing import Optional
from loguru import logger

from pantheon.extractors.base import BaseExtractor, ModelSignal
from pantheon.mmci.models import Direction


class HuggingFaceExtractor(BaseExtractor):
    """
    Free cloud LLM extractor using HuggingFace Inference API.
    
    Advantages:
    - 100% free (free tier)
    - No local GPU required
    - Access to many models (Llama, Mistral, Qwen, etc.)
    - Good for users without powerful hardware
    
    Disadvantages:
    - Rate limited (30 req/hour free tier)
    - Queue-based (can be slow during peak times)
    - Token limits (10k tokens/month free)
    
    Best for: Supplementing other models, testing different architectures
    """
    
    model_id = "huggingface"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
        timeout: int = 60
    ):
        """
        Initialize HuggingFace extractor.
        
        Args:
            api_key: HuggingFace API key (from .env or None for anonymous)
            model_name: HuggingFace model repo (default: Mistral-7B-Instruct)
                Popular free options:
                - mistralai/Mistral-7B-Instruct-v0.3
                - meta-llama/Llama-3.2-3B-Instruct
                - Qwen/Qwen2.5-7B-Instruct
            timeout: Request timeout in seconds (default: 60)
        """
        from pantheon.config.settings import settings
        
        self.api_key = api_key or getattr(settings, 'HUGGINGFACE_API_KEY', None)
        self.model_name = model_name
        self.timeout = timeout
        self.logger = logger.bind(name=f"HuggingFace-{model_name.split('/')[-1]}")
        
        if not self.api_key:
            self.logger.warning("No HuggingFace API key set. Using anonymous tier (very limited).")
    
    async def _call_model(self, prompt: str) -> str:
        """Call HuggingFace Inference API with prompt."""
        try:
            import aiohttp
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.3,
                    "return_full_text": False,
                }
            }
            
            api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 503:
                        # Model loading - common for free tier
                        self.logger.warning(f"Model {self.model_name} is loading. Try again in 30s.")
                        raise Exception("Model loading")
                    
                    result = await response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get('generated_text', '')
                    elif isinstance(result, dict):
                        return result.get('generated_text', str(result))
                    else:
                        raise Exception(f"Unexpected response: {result}")
                        
        except Exception as e:
            self.logger.error(f"HuggingFace call failed: {e}")
            raise
    
    def _parse(self, raw: str) -> ModelSignal:
        """Parse HuggingFace response into ModelSignal."""
        return super()._parse(raw)
