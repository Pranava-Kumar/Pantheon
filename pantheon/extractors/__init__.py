from pantheon.extractors.gemini_pro import GeminiProExtractor
from pantheon.extractors.gemini_flash import GeminiFlashExtractor
from pantheon.extractors.groq_qwen import GroqQwenExtractor
from pantheon.extractors.groq_llama import GroqLlamaExtractor
from pantheon.extractors.groq_gpt import GroqGPTExtractor

def get_all_extractors():
    return [
        GeminiProExtractor(),
        GeminiFlashExtractor(),
        GroqQwenExtractor(),
        GroqLlamaExtractor(),
        GroqGPTExtractor(),
    ]
