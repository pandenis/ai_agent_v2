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