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

    def test_ttl_policy_allows_none_for_permanent(self):
        """Test: TTLPolicy allows None ttl_days for permanent facts"""
        from app.services.ttl_policy import TTLPolicy

        # Arrange & Act
        policy = TTLPolicy(
            fact_type="static",
            default_ttl_days=None,
            description="Permanent facts - never expire"
        )

        # Assert
        assert policy.default_ttl_days is None

class TestDefaultPolicies:
    """Test default TTL policies for each fact type"""

    def test_default_policies_exist(self):
        """Test: DEFAULT_POLICIES dict exists with all fact types"""
        from app.services.ttl_policy import DEFAULT_POLICIES

        # Assert all fact types have policies
        expected_types = ["static", "weather", "event", "preference", "knowledge"]

        for fact_type in expected_types:
            assert fact_type in DEFAULT_POLICIES, f"Missing policy for {fact_type}"

    def test_static_policy_never_expires(self):
        """Test: static facts never expire (ttl_days=None)"""
        from app.services.ttl_policy import DEFAULT_POLICIES

        policy = DEFAULT_POLICIES["static"]

        assert policy.fact_type == "static"
        assert policy.default_ttl_days is None

    def test_weather_policy_expires_daily(self):
        """Test: weather facts expire after 1 day"""
        from app.services.ttl_policy import DEFAULT_POLICIES

        policy = DEFAULT_POLICIES["weather"]

        assert policy.fact_type == "weather"
        assert policy.default_ttl_days == 1

    def test_event_policy_expires_monthly(self):
        """Test: event facts expire after 30 days"""
        from app.services.ttl_policy import DEFAULT_POLICIES

        policy = DEFAULT_POLICIES["event"]

        assert policy.fact_type == "event"
        assert policy.default_ttl_days == 30