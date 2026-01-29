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