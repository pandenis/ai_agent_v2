"""
Agent configuration system for multi-model support
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(Enum):
    """Types of AI agents"""

    LOCAL_OLLAMA = "local_ollama"
    LOCAL_LLAMA_CPP = "local_llama_cpp"
    CLOUD_API = "cloud_api"


class TaskType(Enum):
    """Task types for intelligent routing"""

    GENERAL_CHAT = "general_chat"
    CODE_ANALYSIS = "code_analysis"
    MEDICAL_QUERY = "medical_query"
    DOCUMENT_ANALYSIS = "document_analysis"
    WEB_RESEARCH = "web_research"
    CREATIVE_WRITING = "creative_writing"
    TRANSLATION = "translation"


@dataclass
class AgentCapability:
    """Agent capability definition"""

    name: str
    confidence: float  # 0.0-1.0 how good at this
    description: str


@dataclass
class AgentConfig:
    """Base configuration for an AI agent"""

    name: str
    description: str
    agent_type: AgentType
    capabilities: List[AgentCapability]
    max_tokens: int = 1000
    temperature: float = 0.7
    languages: List[str] = field(default_factory=lambda: ["en"])
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_capability_score(self, task_type: TaskType) -> float:
        """Get confidence score for a specific task type"""
        for cap in self.capabilities:
            if cap.name.lower() == task_type.value.lower():
                return cap.confidence
        return 0.0


@dataclass
class OllamaAgentConfig(AgentConfig):
    """Configuration for Ollama-based agents"""

    base_url: str = "http://localhost:11434"
    model_name: str = "mistral"

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        base_url: str = "http://localhost:11434",
        model_name: str = "mistral",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        languages: List[str] = None,
        enabled: bool = True,
        metadata: Dict[str, Any] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            agent_type=AgentType.LOCAL_OLLAMA,
            capabilities=capabilities,
            max_tokens=max_tokens,
            temperature=temperature,
            languages=languages or ["en"],
            enabled=enabled,
            metadata=metadata or {},
        )
        self.base_url = base_url
        self.model_name = model_name


@dataclass
class LlamaCppAgentConfig(AgentConfig):
    """Configuration for llama.cpp agents"""

    model_path: str = ""
    n_ctx: int = 2048
    n_threads: int = 4

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        model_path: str = "",
        n_ctx: int = 2048,
        n_threads: int = 4,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        languages: List[str] = None,
        enabled: bool = True,
        metadata: Dict[str, Any] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            agent_type=AgentType.LOCAL_LLAMA_CPP,
            capabilities=capabilities,
            max_tokens=max_tokens,
            temperature=temperature,
            languages=languages or ["en"],
            enabled=enabled,
            metadata=metadata or {},
        )
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads


@dataclass
class CloudAgentConfig(AgentConfig):
    """Configuration for cloud API agents"""

    api_base_url: str = ""
    api_key: str = ""
    model_id: str = ""
    rate_limit_rpm: int = 60  # requests per minute

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        api_base_url: str = "",
        api_key: str = "",
        model_id: str = "",
        rate_limit_rpm: int = 60,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        languages: List[str] = None,
        enabled: bool = True,
        metadata: Dict[str, Any] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            agent_type=AgentType.CLOUD_API,
            capabilities=capabilities,
            max_tokens=max_tokens,
            temperature=temperature,
            languages=languages or ["en"],
            enabled=enabled,
            metadata=metadata or {},
        )
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.model_id = model_id
        self.rate_limit_rpm = rate_limit_rpm


# ============================================================================
# AGENT CONFIGURATIONS
# ============================================================================

MISTRAL_CONFIG = OllamaAgentConfig(
    name="Mistral",
    description="Fast, instruction-following general purpose model",
    base_url="http://localhost:11434",
    model_name="mistral:7b-instruct",
    capabilities=[
        AgentCapability("general_chat", 0.9, "Excellent for general conversation"),
        AgentCapability("document_analysis", 0.7, "Good at document understanding"),
        AgentCapability("creative_writing", 0.8, "Strong creative capabilities"),
    ],
    max_tokens=1000,
    temperature=0.7,
    languages=["en", "ru", "fr", "es"],
    metadata={"speed": "fast", "size": "7B"},
)

DEEPSEEK_CONFIG = LlamaCppAgentConfig(
    name="DeepSeek",
    description="Code-specialized model with strong technical capabilities",
    model_path="models/deepseek-coder-7b.gguf",
    capabilities=[
        AgentCapability("code_analysis", 1.0, "Exceptional code understanding"),
        AgentCapability("general_chat", 0.6, "Basic conversation ability"),
        AgentCapability("document_analysis", 0.8, "Strong technical docs analysis"),
    ],
    max_tokens=1500,
    temperature=0.3,
    n_ctx=4096,
    languages=["en"],
    metadata={"specialty": "code", "size": "7B"},
)

LLAMA3_CONFIG = OllamaAgentConfig(
    name="Llama3",
    description="Balanced model with strong reasoning capabilities",
    base_url="http://localhost:11434",
    model_name="llama3:8b",
    capabilities=[
        AgentCapability("general_chat", 0.85, "Strong general conversation"),
        AgentCapability("document_analysis", 0.85, "Excellent document understanding"),
        AgentCapability("web_research", 0.8, "Good at synthesizing information"),
        AgentCapability("creative_writing", 0.75, "Solid creative output"),
    ],
    max_tokens=1000,
    temperature=0.7,
    languages=["en", "es", "fr", "de", "it"],
    metadata={"speed": "medium", "size": "8B", "quality": "high"},
)

GROQ_CONFIG = CloudAgentConfig(
    name="Groq",
    description="High-performance cloud model for complex tasks",
    api_base_url="https://api.groq.com/openai/v1",
    api_key="",  # Will be loaded from env
    model_id="llama-3.3-70b-versatile",
    capabilities=[
        AgentCapability("general_chat", 0.95, "Exceptional conversation quality"),
        AgentCapability("code_analysis", 0.9, "Very strong code understanding"),
        AgentCapability("document_analysis", 0.95, "Excellent document analysis"),
        AgentCapability("web_research", 0.95, "Outstanding synthesis"),
        AgentCapability("creative_writing", 0.9, "High-quality creative output"),
    ],
    max_tokens=2000,
    temperature=0.7,
    rate_limit_rpm=30,
    languages=["en", "es", "fr", "de", "it", "pt"],
    metadata={"speed": "very_fast", "size": "70B", "quality": "premium", "cost": "paid"},
)

MEDICAL_CONFIG = OllamaAgentConfig(
    name="Medical",
    description="Specialized medical AI with health knowledge (educational only)",
    base_url="http://localhost:11434",
    model_name="medllama2",
    capabilities=[
        AgentCapability("medical_query", 1.0, "Specialized medical knowledge"),
        AgentCapability("general_chat", 0.5, "Limited general conversation"),
    ],
    max_tokens=800,
    temperature=0.4,
    languages=["en"],
    metadata={"specialty": "medical", "disclaimer": "Educational only - not medical advice", "safety": "high"},
)

GPT_OSS_CONFIG = OllamaAgentConfig(
    name="GPT-OSS",
    description="OpenAI's open-weight model with advanced reasoning for memory analysis",
    base_url="http://localhost:11434",
    model_name="gpt-oss:20b",
    capabilities=[
        AgentCapability("fact_extraction", 1.0, "Superior fact extraction with chain-of-thought"),
        AgentCapability("memory_analysis", 1.0, "Deep memory analysis and reasoning"),
        AgentCapability("general_chat", 0.85, "Strong general conversation"),
        AgentCapability("code_analysis", 0.8, "Good code understanding"),
        AgentCapability("document_analysis", 0.9, "Excellent document comprehension"),
    ],
    max_tokens=2000,
    temperature=0.3,  # Lower temperature for more deterministic fact extraction
    languages=["en", "ru"],
    metadata={
        "reasoning_levels": ["low", "medium", "high"],
        "supports_structured_output": True,
        "supports_function_calling": True,
        "memory_usage": "16GB",
        "specialty": "memory_management",
        "chain_of_thought": True,
    },
)


class AgentRegistry:
    """Central registry for all available agents"""

    def __init__(self):
        self._agents: Dict[str, AgentConfig] = {
            "mistral": MISTRAL_CONFIG,
            "deepseek": DEEPSEEK_CONFIG,
            "llama3": LLAMA3_CONFIG,
            "groq": GROQ_CONFIG,
            "medical": MEDICAL_CONFIG,
            "gpt-oss": GPT_OSS_CONFIG,
        }

    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get configuration for an agent"""
        return self._agents.get(name.lower())

    def list_agents(self, enabled_only: bool = True) -> List[str]:
        """List all available agents"""
        agents = list(self._agents.keys())
        if enabled_only:
            agents = [name for name, config in self._agents.items() if config.enabled]
        return agents

    def find_best_agent_for_task(self, task_type: TaskType) -> Optional[str]:
        """Find the best agent for a specific task type"""
        best_agent = None
        best_score = 0.0

        for name, config in self._agents.items():
            if not config.enabled:
                continue

            score = config.get_capability_score(task_type)
            if score > best_score:
                best_score = score
                best_agent = name

        return best_agent

    def register_agent(self, config: AgentConfig):
        """Register a new agent configuration"""
        self._agents[config.name.lower()] = config

    def disable_agent(self, name: str):
        """Disable an agent"""
        if name.lower() in self._agents:
            self._agents[name.lower()].enabled = False

    def enable_agent(self, name: str):
        """Enable an agent"""
        if name.lower() in self._agents:
            self._agents[name.lower()].enabled = True


# Global registry instance
agent_registry = AgentRegistry()
