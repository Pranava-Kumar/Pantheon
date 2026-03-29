"""
Ollama Mistral Extractor - Free Local LLM for Stock Analysis

Uses Ollama to run Mistral 7B locally (100% free, no API costs).
Mistral is known for excellent reasoning and financial analysis capabilities.

Setup:
1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh
2. Download model: ollama pull mistral:7b
3. Start server: ollama serve
"""

from pantheon.extractors.ollama_llama import OllamaLlamaExtractor


class OllamaMistralExtractor(OllamaLlamaExtractor):
    """
    Free local LLM extractor using Ollama + Mistral 7B.
    
    Mistral 7B advantages:
    - Excellent reasoning capabilities
    - Good for financial analysis
    - Balanced speed/accuracy (7B parameters)
    - Works well with 8GB+ RAM
    
    Recommended for: Fundamental analysis, detailed reasoning
    """
    
    model_id = "ollama_mistral"
    
    def __init__(self, model_name: str = "mistral:7b", timeout: int = 60):
        """
        Initialize Ollama Mistral extractor.
        
        Args:
            model_name: Ollama model tag (default: mistral:7b)
            timeout: Request timeout in seconds (default: 60)
        """
        super().__init__(model_name=model_name, timeout=timeout)
        self.logger = self.logger.bind(name=f"OllamaMistral-{model_name}")
