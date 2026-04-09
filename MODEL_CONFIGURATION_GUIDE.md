# 🤖 Dynamic Model Configuration Guide

## Overview
Your tae-model project now supports **dynamic model selection**. Switch between different LLM models by simply changing environment variables in `.env`.

---

## Supported Models

| Model | Status | Configuration |
|-------|--------|-----------------|
| **Ollama (phi3:mini)** | ✅ Fully Supported | `USE_PHI3_MINI=true` |
| **Google Gemini** | ✅ Fully Supported | `USE_GEMINI=true` |
| **Mistral** | ✅ Fully Supported | `USE_MISTRAL=true` |

---

## Setup Instructions

### 1️⃣ Option A: Using Ollama (phi3:mini) - LOCAL

**Best for:** Development, free, fast, no API keys needed

**Installation:**
```bash
# Download Ollama from: https://ollama.ai
# Install and run Ollama in background
ollama serve

# In a new terminal, pull phi3:mini
ollama pull phi3:mini
```

**Update .env:**
```env
USE_PHI3_MINI=true
USE_GEMINI=false
USE_MISTRAL=false

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:mini
```

---

### 2️⃣ Option B: Using Google Gemini - CLOUD

**Best for:** Production, powerful, requires API key

**Installation:**
```bash
# Get API key from: https://aistudio.google.com/app/apikeys
pip install google-generativeai
```

**Update .env:**
```env
USE_PHI3_MINI=false
USE_GEMINI=true
USE_MISTRAL=false

GEMINI_API_KEY=your_actual_api_key_here
```

---

### 3️⃣ Option C: Using Mistral - CLOUD

**Best for:** Production, creative, requires API key

**Installation:**
```bash
# Get API key from: https://console.mistral.ai
pip install mistralai
```

**Update .env:**
```env
USE_PHI3_MINI=false
USE_GEMINI=false
USE_MISTRAL=true

MISTRAL_API_KEY=your_actual_api_key_here
```

---

## Quick Start

### Step 1: Update .env
Choose ONE model and enable it:
```env
# Option 1: Ollama (recommended for development)
USE_PHI3_MINI=true
USE_GEMINI=false
USE_MISTRAL=false

# Option 2: Gemini (recommended for production)
# USE_PHI3_MINI=false
# USE_GEMINI=true
# USE_MISTRAL=false
```

### Step 2: Ensure Model is Running/Available
- **Ollama:** Run `ollama serve` in a separate terminal
- **Gemini/Mistral:** API keys set in .env

### Step 3: Run Your Application
```bash
cd d:\CampusGPT_2.0\tae_model
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Code Usage

The model is **automatically routed** through the `call_llm()` function.

### Before (Hardcoded):
```python
import ollama

response = ollama.chat(
    model="phi3:mini",
    messages=[{"role": "user", "content": prompt}]
)
```

### After (Dynamic):
```python
from app.services.model_config import call_llm

response = call_llm(prompt, temperature=0.7)
```

---

## Updated Files

| File | Changes |
|------|---------|
| `.env` | Added model configuration flags |
| `app/services/model_config.py` | NEW: Dynamic model selector |
| `app/services/question_generator.py` | Updated to use `call_llm()` |
| `app/services/assignment_generator.py` | Updated to use `call_llm()` |

---

## Verification

### Run Setup Check:
```bash
python -c "from app.services.model_config import print_model_config; print_model_config()"
```

### Expected Output (if Ollama):
```
============================================================
🤖 MODEL CONFIGURATION
============================================================
Active Model:  ollama
Phi3:Mini:     ✅ Enabled
Gemini:        ❌ Disabled
Mistral:       ❌ Disabled
Ollama Model:  phi3:mini
Ollama Host:   http://localhost:11434
============================================================
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No model enabled` | Set ONE of `USE_PHI3_MINI`, `USE_GEMINI`, `USE_MISTRAL` to `true` |
| `Connection refused port 11434` | Run `ollama serve` in separate terminal |
| `GEMINI_API_KEY not set` | Add valid API key to `.env` or disable Gemini |
| `Model not found: phi3:mini` | Run `ollama pull phi3:mini` |
| `ModuleNotFoundError: google.generativeai` | Run `pip install google-generativeai` |

---

## Performance Notes

| Model | Speed | Cost | Quality |
|-------|-------|------|---------|
| phi3:mini (Ollama) | Fast ⚡ | Free | Good |
| Gemini | Medium | Pay-per-use | Excellent |
| Mistral | Medium | Pay-per-use | Excellent |

---

## API Reference

### `call_llm(prompt, temperature=0.7)`
Universal LLM interface - automatically routes to configured model.

**Parameters:**
- `prompt` (str): The prompt to send
- `temperature` (float): 0.0-1.0, controls randomness

**Returns:**
- `str`: Response text

**Example:**
```python
from app.services.model_config import call_llm

result = call_llm("What is machine learning?", temperature=0.5)
print(result)
```

---

## Environment Template (.env)

```env
# MODEL CONFIGURATION (DYNAMIC LLM SELECTION)
USE_PHI3_MINI=true
USE_GEMINI=false
USE_MISTRAL=false

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# Google Gemini Configuration
GEMINI_API_KEY=your_key_here

# Mistral Configuration
MISTRAL_API_KEY=your_key_here
```

---

## Support

For issues or questions:
1. Check `.env` configuration
2. Verify model is running (for Ollama)
3. Check API keys (for cloud models)
4. Run diagnostic: `python -m app.services.model_config`
