from .gemini_pro import GeminiProExtractor
from .gemini_flash import GeminiFlashExtractor
from .groq_qwen import GroqQwenExtractor
from .groq_llama import GroqLlamaExtractor
from .groq_gpt import GroqGPTExtractor

def get_all_extractors():
    return [
        GeminiProExtractor(),
        GeminiFlashExtractor(),
        GroqQwenExtractor(),
        GroqLlamaExtractor(),
        GroqGPTExtractor(),
    ]
