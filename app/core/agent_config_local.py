"""
Local model configuration overrides for production
"""
from app.core.agent_config import (
    MISTRAL_CONFIG, DEEPSEEK_CONFIG, LLAMA3_CONFIG, 
    GROQ_CONFIG, MEDICAL_CONFIG, agent_registry
)

# Update Medical config to use your model
MEDICAL_CONFIG.model_name = "thewindmom/llama3-med42-8b:latest"

# Update DeepSeek config
DEEPSEEK_CONFIG.model_name = "deepseek-coder:latest"

# Enable models we have
MISTRAL_CONFIG.enabled = True
LLAMA3_CONFIG.enabled = True
MEDICAL_CONFIG.enabled = True
DEEPSEEK_CONFIG.enabled = True
GROQ_CONFIG.enabled = False

print("✅ Local model configuration loaded")
