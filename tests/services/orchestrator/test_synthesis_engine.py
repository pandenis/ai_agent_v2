"""
Tests for SynthesisEngine - Combines multiple sources into coherent response
"""
import pytest
from app.services.orchestrator.synthesis_engine import (
    SynthesisEngine,
    SynthesisResult
)


class TestSynthesisEngine:
    """Tests for multi-source synthesis"""

    def test_engine_exists(self):
        """Test: SynthesisEngine class can be instantiated"""
        engine = SynthesisEngine()
        assert engine is not None

    def test_synthesize_returns_result(self):
        """Test: synthesize returns SynthesisResult object"""
        engine = SynthesisEngine()

        result = engine.synthesize(
            memory_facts=[{"text": "User prefers Italian food", "confidence": 0.9}],
            web_results=[],
            ai_analysis="Based on your preferences, I recommend trying pasta."
        )

        assert isinstance(result, SynthesisResult)
        assert result.text is not None
        assert 0 <= result.confidence <= 1

    def test_synthesize_memory_only(self):
        """Test: Synthesis with only memory facts (no web, no AI)"""
        engine = SynthesisEngine()

        result = engine.synthesize(
            memory_facts=[
                {"text": "User lives in Tokyo", "confidence": 0.95},
                {"text": "User speaks Japanese", "confidence": 0.85}
            ],
            web_results=[],
            ai_analysis=""
        )

        assert "memory" in result.sources_used
        assert result.confidence > 0.8  # High confidence from memory

    def test_synthesize_with_web_results(self):
        """Test: Synthesis includes web search results"""
        engine = SynthesisEngine()

        result = engine.synthesize(
            memory_facts=[],
            web_results=[
                {"title": "Weather Tokyo", "snippet": "Sunny, 22°C today"},
                {"title": "Tokyo Forecast", "snippet": "Clear skies expected"}
            ],
            ai_analysis="The weather in Tokyo is pleasant today."
        )

        assert "web" in result.sources_used
        assert result.text is not None

    def test_synthesize_combines_all_sources(self):
        """Test: Synthesis combines memory + web + AI analysis"""
        engine = SynthesisEngine()

        result = engine.synthesize(
            memory_facts=[
                {"text": "User has high blood pressure", "confidence": 0.9}
            ],
            web_results=[
                {"title": "Mediterranean Diet Benefits", "snippet": "Reduces heart disease risk by 30%"}
            ],
            ai_analysis="The Mediterranean diet would be beneficial for your condition."
        )

        # All sources should be used
        assert "memory" in result.sources_used
        assert "web" in result.sources_used
        assert "ai" in result.sources_used
        assert len(result.sources_used) == 3

    def test_confidence_higher_with_more_sources(self):
        """Test: Confidence increases when multiple sources agree"""
        engine = SynthesisEngine()

        # Single source
        result_single = engine.synthesize(
            memory_facts=[{"text": "Fact", "confidence": 0.8}],
            web_results=[],
            ai_analysis=""
        )

        # Multiple sources
        result_multi = engine.synthesize(
            memory_facts=[{"text": "Fact about diet", "confidence": 0.8}],
            web_results=[{"title": "Diet info", "snippet": "Confirmed fact"}],
            ai_analysis="This is accurate based on research."
        )

        assert result_multi.confidence >= result_single.confidence

    def test_empty_sources_returns_low_confidence(self):
        """Test: No sources results in low confidence"""
        engine = SynthesisEngine()

        result = engine.synthesize(
            memory_facts=[],
            web_results=[],
            ai_analysis=""
        )

        assert result.confidence < 0.5
        assert len(result.sources_used) == 0