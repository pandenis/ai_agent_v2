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
    pass