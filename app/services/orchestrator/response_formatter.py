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
    def format_direct(self, facts: list[dict]) -> str:
        """Format direct answer from memory facts"""
        if len(facts) == 1:
            return facts[0]["text"] + "."
        return ""