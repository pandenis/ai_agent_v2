"""
Tests for security validation with legitimate prompts
TDD: BUG-06 - Overly strict prompt validation
"""

import pytest
from app.core.security import SecurityValidator


class TestSecurityValidatorLegitimatePrompts:
    """Tests that legitimate prompts are not blocked"""

    def test_allows_environment_variable_questions(self):
        """Prompts asking about $HOME, $PATH should be allowed"""
        prompts = [
            "What does $HOME mean in bash?",
            "How do I use $PATH in Linux?",
            "Explain $USER environment variable",
        ]
        
        for prompt in prompts:
            # Should not raise exception
            result = SecurityValidator.validate_prompt(prompt)
            assert result is not None, f"Should allow: {prompt}"

    def test_allows_price_with_dollar(self):
        """Dollar sign in prices should be allowed"""
        prompts = [
            "The price is $100",
            "Cost: $50.99",
        ]
        
        for prompt in prompts:
            result = SecurityValidator.validate_prompt(prompt)
            assert result is not None, f"Should allow: {prompt}"

    def test_allows_pipe_explanations(self):
        """Pipe character in explanations should be allowed"""
        prompts = [
            "Explain the pipe operator |",
            "What does | mean in bash?",
        ]
        
        for prompt in prompts:
            result = SecurityValidator.validate_prompt(prompt)
            assert result is not None, f"Should allow: {prompt}"

    def test_blocks_actual_command_substitution(self):
        """Real command substitution attacks should still be blocked"""
        dangerous = [
            "$(cat /etc/passwd)",
            "$(rm -rf /)",
        ]
        
        for prompt in dangerous:
            with pytest.raises(Exception):
                SecurityValidator.validate_prompt(prompt)

    def test_blocks_command_chaining(self):
        """Command chaining with dangerous commands should be blocked"""
        dangerous = [
            "; rm -rf /",
            "; cat /etc/passwd",
        ]
        
        for prompt in dangerous:
            with pytest.raises(Exception):
                SecurityValidator.validate_prompt(prompt)
