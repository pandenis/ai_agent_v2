"""
ResponseFormatter - Formats orchestrator responses for better readability.

This module provides formatting utilities for all three response strategies:
- Direct: Memory-only responses with clean formatting
- Enhanced: AI responses with memory context enrichment
- Deep Reasoning: Structured multi-paragraph responses

Usage:
    >>> formatter = ResponseFormatter()
    >>> facts = [{"text": "User's name is Denis", "confidence": 0.95}]
    >>> result = formatter.format_direct(facts)
"""


class ResponseFormatter:
    """Formats responses for better readability"""

    def format_direct(
            self,
            facts: list[dict],
            include_source: bool = False
    ) -> str:
        """Format direct answer from memory facts

        Args:
            facts: List of fact dictionaries with 'text' and 'confidence'
            include_source: If True, append source attribution

        Returns:
            Formatted string with facts and optional source
        """
        if len(facts) == 1:
            answer = facts[0]["text"] + "."
            if include_source:
                answer += " (from memory)"
            return answer

        # Multiple facts: bullet list
        formatted = "Here's what I know:\n\n"
        for fact in facts:
            formatted += f"• {fact['text']}\n"

        if include_source:
            formatted += "\n(from memory)"

        return formatted.strip()

    def format_enhanced(
            self,
            ai_response: str,
            context_facts: list[dict]
    ) -> str:
        """Format enhanced answer with memory context

        Args:
            ai_response: Response from AI agent
            context_facts: Relevant facts from memory for context

        Returns:
            Formatted string with AI response and context
        """
        formatted = ai_response + "\n\n"

        if context_facts:
            formatted += "Based on what I know about you:\n"
            for fact in context_facts[:3]:  # Top 3 most relevant facts
                formatted += f"• {fact['text']}\n"

        return formatted.strip()