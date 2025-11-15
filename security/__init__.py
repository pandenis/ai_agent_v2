"""
Security Module
AI Agent v2 - Security Layer
Created: November 15, 2025

This module provides input validation and sanitization
to prevent injection attacks and ensure system security.
"""

from .input_validation import (
    SecurityValidator,
    SecureLogger,
    validate_input,
    validate_file,
    sanitize_log_message
)

__all__ = [
    'SecurityValidator',
    'SecureLogger',
    'validate_input',
    'validate_file',
    'sanitize_log_message'
]

__version__ = '1.0.0'