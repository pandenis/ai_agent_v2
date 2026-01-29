"""
TTL Policy configuration for memory fact lifecycle management.

Task 3.2: Create TTL policy configuration per memory/fact type

Defines default TTL (time-to-live) policies for different fact types,
enabling automatic expiration of facts based on their nature.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.memory_v2 import Fact

@dataclass
class TTLPolicy:
    """
    TTL policy for a specific fact type.

    Attributes:
        fact_type: The fact type this policy applies to
        default_ttl_days: Default TTL in days (None = never expires)
        description: Human-readable description of the policy
    """
    fact_type: str
    default_ttl_days: Optional[int]
    description: str

# Default TTL policies per fact type
DEFAULT_POLICIES = {
    "static": TTLPolicy(
        fact_type="static",
        default_ttl_days=None,
        description="Permanent facts - name, identity, never expire"
    ),
    "weather": TTLPolicy(
        fact_type="weather",
        default_ttl_days=1,
        description="Weather info - expires daily"
    ),
    "event": TTLPolicy(
        fact_type="event",
        default_ttl_days=30,
        description="Events - expire after 30 days"
    ),
    "preference": TTLPolicy(
        fact_type="preference",
        default_ttl_days=None,
        description="User preferences - permanent"
    ),
    "knowledge": TTLPolicy(
        fact_type="knowledge",
        default_ttl_days=90,
        description="Learned facts - 90 day refresh cycle"
    ),
}

def get_policy_for_fact_type(fact_type: str) -> TTLPolicy:
    """
    Get TTL policy for a specific fact type.

    Args:
        fact_type: The fact type to get policy for

    Returns:
        TTLPolicy for the fact type, or default (static) if unknown
    """
    return DEFAULT_POLICIES.get(fact_type, DEFAULT_POLICIES["static"])

def calculate_expires_at(created: datetime, ttl_days: Optional[int]) -> Optional[datetime]:
    """
    Calculate expiration timestamp based on creation time and TTL.

    Args:
        created: When the fact was created
        ttl_days: Time-to-live in days (None = never expires)

    Returns:
        Expiration datetime, or None if ttl_days is None
    """
    if ttl_days is None:
        return None
    return created + timedelta(days=ttl_days)

def apply_ttl_policy(fact: "Fact") -> "Fact":
    """
    Apply TTL policy to a fact based on its fact_type.

    Sets ttl_days and expires_at based on the default policy
    for the fact's type.

    Args:
        fact: Fact to apply policy to

    Returns:
        The fact with ttl_days and expires_at set
    """
    policy = get_policy_for_fact_type(fact.fact_type)
    fact.ttl_days = policy.default_ttl_days
    fact.expires_at = calculate_expires_at(fact.created, fact.ttl_days)
    return fact