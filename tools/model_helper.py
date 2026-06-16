"""
tools/model_helper.py
---------------------
Helper functions to resolve and fallback to available Gemini models dynamically.
"""
import os
import google.generativeai as genai

# Cache for available models
_AVAILABLE_MODELS = None

def get_available_model(env_var_name: str, fallback_default: str = "gemini-2.5-flash") -> str:
    """
    Returns the best available Gemini model.
    1. Checks the specified environment variable (e.g. GEMINI_MODEL).
    2. Verifies if that model is supported by the user's API key/quota.
    3. If not supported, finds the next best available model from the API.
    4. Falls back to a default model if listing fails or no match is found.
    """
    global _AVAILABLE_MODELS
    
    preferred_name = os.getenv(env_var_name)
    if not preferred_name:
        preferred_name = os.getenv("GEMINI_MODEL") or fallback_default
        
    # Standardize names (strip 'models/' prefix for comparison)
    def clean_name(name: str) -> str:
        if name.startswith("models/"):
            return name[7:]
        return name

    cleaned_preferred = clean_name(preferred_name)

    # Fetch available models if not already cached
    if _AVAILABLE_MODELS is None:
        try:
            # Re-configure just in case
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            models = genai.list_models()
            _AVAILABLE_MODELS = [clean_name(m.name) for m in models if "generateContent" in m.supported_generation_methods]
        except Exception as e:
            # Print a quiet warning and fallback to hardcoded list
            print(f"  [WARN] Failed to list models from Gemini API: {e}")
            _AVAILABLE_MODELS = [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-pro-latest"
            ]

    # Case 1: Preferred model is directly available
    if cleaned_preferred in _AVAILABLE_MODELS:
        return cleaned_preferred

    # Case 2: Preferred model contains a version that matches something in the list
    for model in _AVAILABLE_MODELS:
        if cleaned_preferred in model or model in cleaned_preferred:
            return model

    # Case 3: Fall back to best available flash model
    for model in _AVAILABLE_MODELS:
        if "flash" in model:
            return model

    # Case 4: Final fallback
    return _AVAILABLE_MODELS[0] if _AVAILABLE_MODELS else fallback_default
