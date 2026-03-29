from pantheon.extractors.gemini_pro import GeminiProExtractor
from pantheon.extractors.gemini_flash import GeminiFlashExtractor
from pantheon.extractors.groq_qwen import GroqQwenExtractor
from pantheon.extractors.groq_llama import GroqLlamaExtractor
from pantheon.extractors.groq_gpt import GroqGPTExtractor
# Ollama models commented out - uncomment when you want to use local LLMs
# from pantheon.extractors.ollama_llama import OllamaLlamaExtractor
# from pantheon.extractors.ollama_mistral import OllamaMistralExtractor
from pantheon.extractors.huggingface import HuggingFaceExtractor

def get_all_extractors(include_local: bool = False, include_cloud: bool = True):
    """
    Get all available LLM extractors.
    
    Args:
        include_local: Include local Ollama models (requires Ollama installed) - DISABLED
        include_cloud: Include cloud APIs (Gemini, Groq, HuggingFace)
    
    Returns:
        List of initialized extractor instances
    """
    extractors = []
    
    # Cloud-based extractors (free tiers)
    if include_cloud:
        extractors.extend([
            GeminiProExtractor(),
            GeminiFlashExtractor(),
            GroqQwenExtractor(),
            GroqLlamaExtractor(),
            GroqGPTExtractor(),
            HuggingFaceExtractor(),
        ])
    
    # Local extractors (100% free, no rate limits) - COMMENTED OUT
    # Uncomment below when you want to use Ollama local models
    # if include_local:
    #     try:
    #         extractors.append(OllamaLlamaExtractor())
    #         extractors.append(OllamaMistralExtractor())
    #     except Exception as e:
    #         from loguru import logger
    #         logger.warning(f"Ollama not available, skipping local models: {e}")
    
    return extractors
