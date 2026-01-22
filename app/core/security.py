"""
Security utilities: input validation, sanitization
"""

import re
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings


class SecurityValidator:
    """Input validation and sanitization"""

    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]",  # Control characters
        # BUG-06 FIX: More targeted patterns - allow $, |, ` in normal context
        r"\$\([^)]*\)",  # Command substitution $(...)
        r";\s*(rm|cat|curl|wget|nc|bash|sh|python|chmod|chown)\b",  # Command chaining with dangerous commands
        r"\|\s*(bash|sh|python)\b",  # Piping to shell interpreters
        r"(?i)(curl|wget|nc|netcat)\s+[a-z]+://",  # Network commands with URLs
    ]

    @classmethod
    def validate_prompt(cls, prompt: str) -> str:
        """
        Validate and sanitize user prompt

        Args:
            prompt: User input text

        Returns:
            Sanitized prompt

        Raises:
            HTTPException: If prompt is invalid or dangerous
        """
        if not prompt or not prompt.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt cannot be empty")

        # Check length
        if len(prompt) > settings.max_prompt_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prompt too long. Maximum {settings.max_prompt_length} characters",
            )

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, prompt):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Input contains potentially dangerous characters"
                )

        return prompt.strip()

    @classmethod
    def validate_session_id(cls, session_id: str) -> str:
        """Validate session ID format"""
        if not re.match(r"^[a-zA-Z0-9_-]{8,64}$", session_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID format")
        return session_id
