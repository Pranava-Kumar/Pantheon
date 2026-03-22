from extractors.gemini_pro import GeminiProExtractor
from extractors.gemini_flash import GeminiFlashExtractor
from extractors.groq_qwen import GroqQwenExtractor
from extractors.groq_llama import GroqLlamaExtractor
from extractors.groq_gpt import GroqGPTExtractor

def get_all_extractors():
    return [
        GeminiProExtractor(),
        GeminiFlashExtractor(),
        GroqQwenExtractor(),
        GroqLlamaExtractor(),
        GroqGPTExtractor(),
    ]
