"""
Tests for SecurityValidator.

Covers:
- Prompt validation (empty, length, dangerous patterns)
- Session ID validation (format, length)
"""

import pytest
from fastapi import HTTPException

from app.core.security import SecurityValidator


class TestValidatePrompt:
    """Tests for validate_prompt method."""

    def test_empty_prompt_raises_exception(self):
        """Test: Empty string raises HTTPException 400."""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_prompt("")

        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    def test_whitespace_only_prompt_raises_exception(self):
        """Test: Whitespace-only string raises HTTPException 400."""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_prompt("   \t\n   ")

        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()

    def test_too_long_prompt_raises_exception(self):
        """Test: Prompt exceeding max length raises HTTPException 400."""
        from app.core.config import settings

        long_prompt = "a" * (settings.max_prompt_length + 1)

        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_prompt(long_prompt)

        assert exc_info.value.status_code == 400
        assert "too long" in exc_info.value.detail.lower()

    def test_control_characters_raises_exception(self):
        """Test: Control characters raise HTTPException 400."""
        dangerous_prompts = [
            "Hello\x00World",  # Null byte
            "Test\x07text",  # Bell character
            "Data\x1fhere",  # Unit separator
        ]

        for prompt in dangerous_prompts:
            with pytest.raises(HTTPException) as exc_info:
                SecurityValidator.validate_prompt(prompt)

            assert exc_info.value.status_code == 400
            assert "dangerous" in exc_info.value.detail.lower()

    def test_shell_injection_chars_raises_exception(self):
        """Test: Shell injection characters raise HTTPException 400."""
        dangerous_prompts = [
            "ls; rm -rf /",  # Semicolon
            "cat file & echo",  # Ampersand
            "test | grep",  # Pipe
            "hello `whoami`",  # Backticks
            "price is $100",  # Dollar sign
        ]

        for prompt in dangerous_prompts:
            with pytest.raises(HTTPException) as exc_info:
                SecurityValidator.validate_prompt(prompt)

            assert exc_info.value.status_code == 400
            assert "dangerous" in exc_info.value.detail.lower()

    def test_command_substitution_raises_exception(self):
        """Test: Command substitution patterns raise HTTPException 400."""
        dangerous_prompts = [
            "$(whoami)",
            "Hello $(cat /etc/passwd)",
            "$(rm -rf /)",
        ]

        for prompt in dangerous_prompts:
            with pytest.raises(HTTPException) as exc_info:
                SecurityValidator.validate_prompt(prompt)

            assert exc_info.value.status_code == 400
            assert "dangerous" in exc_info.value.detail.lower()