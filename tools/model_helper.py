"""Model helper utility for resolving Gemini models."""
import os
import google.generativeai as genai

_AVAILABLE_MODELS = None

def get_available_model(env_var_name: str, fallback_default: str = "gemini-2.5-flash") -> str:
    """Get the best available Gemini model from environment or API list."""
    global _AVAILABLE_MODELS
    
    preferred_name = os.getenv(env_var_name)
    if not preferred_name:
        preferred_name = os.getenv("GEMINI_MODEL") or fallback_default
        
    def clean_name(name: str) -> str:
        if name.startswith("models/"):
            return name[7:]
        return name

    cleaned_preferred = clean_name(preferred_name)

    if _AVAILABLE_MODELS is None:
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            models = genai.list_models()
            _AVAILABLE_MODELS = [clean_name(m.name) for m in models if "generateContent" in m.supported_generation_methods]
        except Exception as e:
            print(f"  [WARN] Failed to list models from Gemini API: {e}")
            _AVAILABLE_MODELS = [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-pro-latest"
            ]

    if cleaned_preferred in _AVAILABLE_MODELS:
        return cleaned_preferred

    for model in _AVAILABLE_MODELS:
        if cleaned_preferred in model or model in cleaned_preferred:
            return model

    for model in _AVAILABLE_MODELS:
        if "flash" in model:
            return model

    return _AVAILABLE_MODELS[0] if _AVAILABLE_MODELS else fallback_default
