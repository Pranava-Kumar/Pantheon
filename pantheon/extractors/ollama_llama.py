"""
Ollama Llama Extractor - Free Local LLM for Stock Analysis

Uses Ollama to run Llama 3.2 locally (100% free, no API costs).
Supports 3B and 7B parameter models for different speed/accuracy tradeoffs.

Setup:
1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh
2. Download model: ollama pull llama3.2:3b
3. Start server: ollama serve
"""

import asyncio
from typing import Optional
from loguru import logger

from pantheon.extractors.base import BaseExtractor, ModelSignal
from pantheon.mmci.models import Direction


class OllamaLlamaExtractor(BaseExtractor):
    """
    Free local LLM extractor using Ollama + Llama 3.2.
    
    Advantages:
    - 100% free (no API costs)
    - Unlimited requests
    - Privacy (data stays local)
    - No rate limits
    
    Disadvantages:
    - Requires local GPU/CPU resources
    - Slower than cloud APIs (3-10 seconds per request)
    - Model quality depends on local model size
    """
    
    model_id = "ollama_llama"
    
    def __init__(self, model_name: str = "llama3.2:3b", timeout: int = 60):
        """
        Initialize Ollama Llama extractor.
        
        Args:
            model_name: Ollama model tag (default: llama3.2:3b)
                Options:
                - llama3.2:3b (fast, low RAM, good for testing)
                - llama3.2:7b (balanced)
                - mistral:7b (good for finance)
                - qwen2.5:7b (excellent for analysis)
            timeout: Request timeout in seconds (default: 60)
        """
        self.model_name = model_name
        self.timeout = timeout
        self.logger = logger.bind(name=f"OllamaLlama-{model_name}")
        
        # Verify Ollama is running
        try:
            import ollama
            ollama.list()
            self.logger.info(f"Ollama connected, using model: {model_name}")
        except Exception as e:
            self.logger.warning(f"Ollama not available: {e}. Install with: curl -fsSL https://ollama.ai/install.sh | sh")
    
    async def _call_model(self, prompt: str) -> str:
        """Call Ollama Llama model with prompt."""
        try:
            import ollama
            
            # Run in thread pool to avoid blocking async event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama.chat(
                    model=self.model_name,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    options={
                        'temperature': 0.3,  # Lower temperature for consistent analysis
                        'num_predict': 500,  # Max tokens
                    }
                )
            )
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Ollama call failed: {e}")
            raise
    
    def _parse(self, raw: str) -> ModelSignal:
        """Parse Ollama response into ModelSignal."""
        return super()._parse(raw)
