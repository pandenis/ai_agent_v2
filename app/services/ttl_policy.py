"""
TTL Policy configuration for memory fact lifecycle management.

Task 3.2: Create TTL policy configuration per memory/fact type

Defines default TTL (time-to-live) policies for different fact types,
enabling automatic expiration of facts based on their nature.
"""

from dataclasses import dataclass
from typing import Optional


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