"""
Unit tests for TTL Policy configuration

Task 3.2: Create TTL policy configuration per memory/fact type
"""

import pytest


class TestTTLPolicyDataclass:
    """Test TTLPolicy dataclass"""

    def test_ttl_policy_has_required_fields(self):
        """Test: TTLPolicy has fact_type, default_ttl_days, description"""
        from app.services.ttl_policy import TTLPolicy

        # Arrange & Act
        policy = TTLPolicy(
            fact_type="weather",
            default_ttl_days=1,
            description="Weather info - expires daily"
        )

        # Assert
        assert policy.fact_type == "weather"
        assert policy.default_ttl_days == 1
        assert policy.description == "Weather info - expires daily"