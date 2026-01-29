"""
Unit tests for TTL Policy configuration

Task 3.2: Create TTL policy configuration per memory/fact type
"""

import pytest
from datetime import datetime, timedelta


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


class TestGetPolicyForFactType:
    """Test get_policy_for_fact_type function"""

    def test_get_policy_returns_correct_policy(self):
        """Test: get_policy_for_fact_type returns matching policy"""
        from app.services.ttl_policy import get_policy_for_fact_type

        policy = get_policy_for_fact_type("weather")

        assert policy.fact_type == "weather"
        assert policy.default_ttl_days == 1

    def test_get_policy_unknown_type_returns_default(self):
        """Test: unknown fact_type returns default policy (static)"""
        from app.services.ttl_policy import get_policy_for_fact_type

        policy = get_policy_for_fact_type("unknown_type")

        assert policy.fact_type == "static"
        assert policy.default_ttl_days is None

class TestCalculateExpiration:
    """Test calculate_expires_at function"""

    def test_calculate_expires_at_with_ttl(self):
        """Test: calculates correct expiration date"""
        from app.services.ttl_policy import calculate_expires_at

        created = datetime(2026, 1, 29, 12, 0, 0)
        ttl_days = 30

        expires_at = calculate_expires_at(created, ttl_days)

        expected = datetime(2026, 2, 28, 12, 0, 0)
        assert expires_at == expected

    def test_calculate_expires_at_none_ttl_returns_none(self):
        """Test: None ttl_days returns None (never expires)"""
        from app.services.ttl_policy import calculate_expires_at

        created = datetime(2026, 1, 29, 12, 0, 0)

        expires_at = calculate_expires_at(created, None)

        assert expires_at is None

class TestApplyPolicyToFact:
    """Test apply_ttl_policy function"""

    def test_apply_policy_sets_ttl_days(self):
        """Test: apply_ttl_policy sets ttl_days from policy"""
        from app.services.ttl_policy import apply_ttl_policy
        from app.models.memory_v2 import Fact

        fact = Fact(
            fact_id="test-1",
            text="Weather is sunny",
            fact_type="weather"
        )

        updated_fact = apply_ttl_policy(fact)

        assert updated_fact.ttl_days == 1  # weather policy

    def test_apply_policy_sets_expires_at(self):
        """Test: apply_ttl_policy calculates expires_at"""
        from app.services.ttl_policy import apply_ttl_policy
        from app.models.memory_v2 import Fact

        fact = Fact(
            fact_id="test-2",
            text="Weather is sunny",
            fact_type="weather"
        )

        updated_fact = apply_ttl_policy(fact)

        assert updated_fact.expires_at is not None
        # Should be ~1 day from created
        delta = updated_fact.expires_at - updated_fact.created
        assert delta.days == 1

    def test_apply_policy_permanent_fact_no_expiration(self):
        """Test: static facts get None for ttl_days and expires_at"""
        from app.services.ttl_policy import apply_ttl_policy
        from app.models.memory_v2 import Fact

        fact = Fact(
            fact_id="test-3",
            text="User's name is Denis",
            fact_type="static"
        )

        updated_fact = apply_ttl_policy(fact)

        assert updated_fact.ttl_days is None
        assert updated_fact.expires_at is None