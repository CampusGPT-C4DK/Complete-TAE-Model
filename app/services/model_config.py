"""
Dynamic Model Configuration System
Handles automatic model selection based on .env configuration
Supports: Ollama (phi3:mini, mistral), Google Gemini, etc.
"""

import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Use settings from Pydantic config
USE_PHI3_MINI = settings.USE_PHI3_MINI
USE_GEMINI = settings.USE_GEMINI
USE_MISTRAL = settings.USE_MISTRAL

OLLAMA_HOST = settings.OLLAMA_HOST
OLLAMA_MODEL = settings.OLLAMA_MODEL

GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL

MISTRAL_API_KEY = settings.MISTRAL_API_KEY

# ==================== MODEL PROVIDER DETECTION ====================

def get_active_model() -> str:
    """
    Detect which model is active based on configuration.
    Returns: 'ollama', 'gemini', 'mistral', or None if no model enabled
    """
    if USE_PHI3_MINI:
        return "ollama"
    elif USE_GEMINI:
        return "gemini"
    elif USE_MISTRAL:
        return "mistral"
    else:
        logger.warning("⚠️ No LLM model enabled! Please set one model to true")
        return None


def validate_model_config() -> bool:
    """
    Validate that the selected model has proper configuration.
    Returns: True if valid, False otherwise
    """
    active_model = get_active_model()
    
    if active_model is None:
        logger.error("❌ No model selected. Set one of: USE_PHI3_MINI, USE_GEMINI, USE_MISTRAL to true")
        return False
    
    if active_model == "ollama":
        logger.info(f"✅ Using Ollama model: {OLLAMA_MODEL}")
        # You can add a ping test here if needed
        return True
    
    elif active_model == "gemini":
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not set in .env")
            return False
        logger.info("✅ Using Google Gemini")
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
        except ImportError:
            logger.error("❌ google-generativeai not installed. Run: pip install google-generativeai")
            return False
        return True
    
    elif active_model == "mistral":
        if not MISTRAL_API_KEY:
            logger.error("❌ MISTRAL_API_KEY not set in .env")
            return False
        logger.info("✅ Using Mistral API")
        return True
    
    return False


# ==================== DYNAMIC LLM INTERFACE ====================

def call_llm(prompt: str, temperature: float = 0.7) -> str:
    """
    Unified LLM interface that automatically routes to the correct model.
    
    Args:
        prompt: The prompt to send to the LLM
        temperature: Model temperature (0.0 to 1.0)
    
    Returns:
        Response text from the model
    """
    active_model = get_active_model()
    
    if active_model is None:
        raise ValueError("No LLM model configured. Check your .env file.")
    
    if active_model == "ollama":
        return _call_ollama(prompt, temperature)
    elif active_model == "gemini":
        return _call_gemini(prompt, temperature)
    elif active_model == "mistral":
        return _call_mistral(prompt, temperature)
    else:
        raise ValueError(f"Unknown model: {active_model}")


def _call_ollama(prompt: str, temperature: float = 0.7) -> str:
    """Call Ollama model (phi3:mini or other local models)"""
    try:
        import ollama
        
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        
        return response["message"]["content"]
    
    except Exception as e:
        logger.error(f"❌ Ollama error: {str(e)}")
        logger.error(f"   Make sure Ollama is running: ollama serve")
        raise


def _call_gemini(prompt: str, temperature: float = 0.7) -> str:
    """Call Google Gemini model"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 2048,
            }
        )
        
        return response.text
    
    except ImportError:
        logger.error("❌ google-generativeai not installed. Run: pip install google-generativeai")
        raise
    except Exception as e:
        logger.error(f"❌ Gemini error: {str(e)}")
        raise


def _call_mistral(prompt: str, temperature: float = 0.7) -> str:
    """Call Mistral API"""
    try:
        from mistralai.client import MistralClient
        
        client = MistralClient(api_key=MISTRAL_API_KEY)
        
        response = client.chat(
            model="mistral-medium",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"❌ Mistral error: {str(e)}")
        raise


# ==================== INFO & DIAGNOSTICS ====================

def get_model_info() -> Dict[str, Any]:
    """Get information about the currently configured model"""
    active = get_active_model()
    
    return {
        "active_model": active,
        "use_phi3_mini": USE_PHI3_MINI,
        "use_gemini": USE_GEMINI,
        "use_mistral": USE_MISTRAL,
        "ollama_model": OLLAMA_MODEL,
        "ollama_host": OLLAMA_HOST,
        "gemini_model": GEMINI_MODEL,
    }


def print_model_config():
    """Print current model configuration to console"""
    info = get_model_info()
    
    print("\n" + "="*60)
    print("🤖 MODEL CONFIGURATION")
    print("="*60)
    print(f"Active Model:  {info['active_model'] or 'NONE (disabled)'}")
    print(f"Phi3:Mini:     {'✅ Enabled' if info['use_phi3_mini'] else '❌ Disabled'}")
    print(f"Gemini:        {'✅ Enabled' if info['use_gemini'] else '❌ Disabled'}")
    print(f"Mistral:       {'✅ Enabled' if info['use_mistral'] else '❌ Disabled'}")
    
    if info['active_model'] == 'ollama':
        print(f"Ollama Model:  {info['ollama_model']}")
        print(f"Ollama Host:   {info['ollama_host']}")
    
    if info['active_model'] == 'gemini':
        print(f"Gemini Model:  {info['gemini_model']}")
    
    print("="*60 + "\n")


# Initialize on import
if __name__ != "__main__":
    print_model_config()
