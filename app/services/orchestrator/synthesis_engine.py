"""
SynthesisEngine - Combines multiple sources into coherent response.

Takes input from:
- Memory facts (user's stored information)
- Web search results (external data)
- AI analysis (model's reasoning)

Produces:
- Combined text response
- Overall confidence score
- Source attribution
- Conflict detection

Usage:
    >>> engine = SynthesisEngine()
    >>> result = engine.synthesize(
    ...     memory_facts=[{"text": "User likes pasta", "confidence": 0.9}],
    ...     web_results=[{"title": "Recipe", "snippet": "Best pasta..."}],
    ...     ai_analysis="I recommend trying carbonara."
    ... )
    >>> print(f"Confidence: {result.confidence}")
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class SynthesisResult:
    """Result of multi-source synthesis"""
    text: str
    confidence: float
    sources_used: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


class SynthesisEngine:
    """Combines multiple sources into coherent response"""

    def synthesize(
            self,
            memory_facts: List[Dict],
            web_results: List[Dict],
            ai_analysis: str
    ) -> SynthesisResult:
        """
        Synthesize response from multiple sources.

        Args:
            memory_facts: Facts from user's memory
            web_results: Results from web search
            ai_analysis: AI model's analysis

        Returns:
            SynthesisResult with combined response and confidence
        """
        sources_used = []
        text_parts = []
        confidence_scores = []

        # Process memory facts
        if memory_facts:
            sources_used.append("memory")
            memory_confidence = sum(
                f.get("confidence", 0.5) for f in memory_facts
            ) / len(memory_facts)
            confidence_scores.append(memory_confidence)

            facts_text = "; ".join(f.get("text", "") for f in memory_facts)
            text_parts.append(f"From memory: {facts_text}")

        # Process web results
        if web_results:
            sources_used.append("web")
            confidence_scores.append(0.7)  # Web has moderate confidence

            web_text = "; ".join(
                f"{r.get('title', '')}: {r.get('snippet', '')}"
                for r in web_results
            )
            text_parts.append(f"From web: {web_text}")

        # Process AI analysis
        if ai_analysis:
            sources_used.append("ai")
            confidence_scores.append(0.75)  # AI has good confidence
            text_parts.append(ai_analysis)

        # Calculate overall confidence
        if confidence_scores:
            # More sources = higher confidence (bonus for agreement)
            base_confidence = sum(confidence_scores) / len(confidence_scores)
            source_bonus = min(0.1 * (len(sources_used) - 1), 0.2)
            confidence = min(base_confidence + source_bonus, 1.0)
        else:
            confidence = 0.3  # Low confidence when no sources

        # Combine text
        if text_parts:
            text = "\n\n".join(text_parts)
        else:
            text = "I don't have enough information to provide a complete answer."

        return SynthesisResult(
            text=text,
            confidence=confidence,
            sources_used=sources_used,
            conflicts=[]  # TODO: Implement conflict detection
        )