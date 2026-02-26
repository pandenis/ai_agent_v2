"""Test: conversation history is injected into the prompt sent to the AI agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.orchestrator.orchestrator import IntelligentOrchestrator
from app.services.orchestrator.memory_evaluator import MemoryEvaluation
from app.services.orchestrator.decision_engine import Decision


class TestContextInThread:

    @pytest.mark.asyncio
    async def test_conversation_history_is_injected_into_prompt(self):
        """History from get_conversation_history() must appear in the prompt sent to the agent."""

        # --- Arrange ---
        # Simple message stub matching ConversationMessage interface (.role, .content)
        class _Msg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        history = [
            _Msg(role="user", content="My name is Denis"),
            _Msg(role="assistant", content="Nice to meet you Denis"),
        ]

        # Mock memory_service
        memory_service = MagicMock()
        memory_service.get_conversation_history = AsyncMock(return_value=history)
        # Sync mock → raises TypeError when awaited → _build_context_with_map falls back to []
        memory_service.search_facts = MagicMock(return_value=[])

        # Capture the prompt passed to agent.generate()
        captured_prompts = []

        async def _fake_generate(prompt):
            captured_prompts.append(prompt)
            return {"response": "Your name is Denis."}

        mock_agent = MagicMock()
        mock_agent.name = "mistral"
        mock_agent.generate = _fake_generate

        mock_agent_factory = MagicMock()
        mock_agent_factory.create_agent = MagicMock(return_value=mock_agent)

        # Build orchestrator
        orchestrator = IntelligentOrchestrator(
            memory_service=memory_service,
            agent_factory=mock_agent_factory,
        )

        # Force "enhanced" strategy: coverage_score in [0.7, 0.9) → Rule 2 in DecisionEngine
        mock_eval = MemoryEvaluation(
            coverage_score=0.8,
            relevant_facts=[],
            gaps=[],
            confidence=0.6,
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        # Prevent _load_memory_map from hitting the real DB
        mock_memory_map = MagicMock()
        mock_memory_map.build_context_for_query = MagicMock(return_value="")
        orchestrator.memory_map = mock_memory_map

        # --- Act ---
        await orchestrator.process_query("What is my name?", session_id="test-123")

        # --- Assert ---
        assert len(captured_prompts) > 0, "agent.generate() was never called"
        prompt_sent = captured_prompts[0]
        assert "Denis" in prompt_sent, (
            f"Expected 'Denis' in the prompt (from conversation history), got:\n{prompt_sent}"
        )

    @pytest.mark.asyncio
    async def test_direct_answer_uses_conversation_history(self):
        """_direct_answer must use conversation history when no facts are available."""

        class _Msg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        history = [
            _Msg(role="user", content="My name is Denis"),
            _Msg(role="assistant", content="Nice to meet you Denis"),
        ]

        memory_service = MagicMock()
        memory_service.get_conversation_history = AsyncMock(return_value=history)
        memory_service.search_facts = MagicMock(return_value=[])

        captured_prompts = []

        async def _fake_generate(prompt):
            captured_prompts.append(prompt)
            return {"response": "Your name is Denis."}

        mock_agent = MagicMock()
        mock_agent.name = "mistral"
        mock_agent.generate = _fake_generate

        mock_agent_factory = MagicMock()
        mock_agent_factory.create_agent = MagicMock(return_value=mock_agent)

        orchestrator = IntelligentOrchestrator(
            memory_service=memory_service,
            agent_factory=mock_agent_factory,
        )

        # coverage_score=0.95 + simple query → "direct" strategy (Rule 1 in DecisionEngine)
        mock_eval = MemoryEvaluation(
            coverage_score=0.95,
            relevant_facts=[],
            gaps=[],
            confidence=0.9,
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        mock_memory_map = MagicMock()
        mock_memory_map.build_context_for_query = MagicMock(return_value="")
        orchestrator.memory_map = mock_memory_map

        # --- Act ---
        result = await orchestrator.process_query("What is my name?", session_id="test-456")

        # --- Assert ---
        assert "Denis" in result["text"] or (
            len(captured_prompts) > 0 and "Denis" in captured_prompts[0]
        ), (
            f"Expected 'Denis' in response or prompt. "
            f"Response: {result['text']!r}, Prompts: {captured_prompts}"
        )

    @pytest.mark.asyncio
    async def test_deep_reasoning_uses_conversation_history(self):
        """conversation_history must appear in the prompt sent during deep_reasoning."""

        class _Msg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        history = [
            _Msg(role="user", content="My name is Denis"),
            _Msg(role="assistant", content="Nice to meet you Denis"),
        ]

        memory_service = MagicMock()
        memory_service.get_conversation_history = AsyncMock(return_value=history)
        memory_service.search_facts = MagicMock(return_value=[])

        captured_prompts = []

        async def _fake_generate(prompt):
            captured_prompts.append(prompt)
            return {"response": "Your name is Denis."}

        mock_agent = MagicMock()
        mock_agent.name = "mixtral"
        mock_agent.generate = _fake_generate

        mock_agent_factory = MagicMock()
        mock_agent_factory.create_agent = MagicMock(return_value=mock_agent)

        orchestrator = IntelligentOrchestrator(
            memory_service=memory_service,
            agent_factory=mock_agent_factory,
        )

        # coverage_score=0.1 → "deep_reasoning" strategy
        mock_eval = MemoryEvaluation(
            coverage_score=0.1,
            relevant_facts=[],
            gaps=["name"],
            confidence=0.1,
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        mock_memory_map = MagicMock()
        mock_memory_map.build_context_for_query = MagicMock(return_value="")
        orchestrator.memory_map = mock_memory_map

        # --- Act ---
        result = await orchestrator.process_query("What is my name?", session_id="test-789")

        # --- Assert ---
        assert "Denis" in result["text"] or (
            len(captured_prompts) > 0 and "Denis" in captured_prompts[0]
        ), (
            f"Expected 'Denis' in response or prompt. "
            f"Response: {result['text']!r}, Prompts: {captured_prompts}"
        )
