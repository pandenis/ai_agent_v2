"""
MemoryAuditor - Duplicate detection and cleanup for Memorisator

Task 39: Deduplicate facts in memory

This service identifies duplicate facts and merges them to:
- Reduce storage waste
- Improve search performance
- Provide cleaner responses to users

Duplicate Detection:
- Uses text similarity (>85% threshold)
- Groups similar facts together
- Identifies exact matches and near-duplicates

Merge Strategy:
- Keep fact with highest importance (primary)
- Combine tags from all duplicates
- Sum usage counts
- Delete non-primary duplicates

Usage:
    auditor = MemoryAuditor()
    duplicates = auditor.find_duplicates(facts)
    for group in duplicates:
        merged = auditor.create_merged_fact(group.facts)
        to_delete = auditor.get_facts_to_delete(group.facts, merged.fact_id)
"""

from dataclasses import dataclass, field
from typing import List, Optional
from difflib import SequenceMatcher

from app.models.memory_v2 import Fact


@dataclass
class DuplicateGroup:
    """Group of duplicate facts with metadata"""
    facts: List[Fact]
    similarity_score: float
    primary_fact_id: Optional[str] = None
    suggested_action: str = "merge"  # merge, manual_review, keep


class MemoryAuditor:
    """
    Auditor for detecting and cleaning up duplicate facts

    Attributes:
        similarity_threshold: Minimum similarity score to consider as duplicate (0.0-1.0)
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize MemoryAuditor

        Args:
            similarity_threshold: Minimum similarity to consider facts as duplicates
        """
        self.similarity_threshold = similarity_threshold

    def find_duplicates(self, facts: List[Fact]) -> List[DuplicateGroup]:
        """
        Find groups of duplicate facts

        Args:
            facts: List of Fact objects to analyze

        Returns:
            List of DuplicateGroup objects containing similar facts
        """
        if len(facts) < 2:
            return []

        duplicate_groups = []
        processed = set()

        for i, fact1 in enumerate(facts):
            if fact1.fact_id in processed:
                continue

            # Find all facts similar to fact1
            similar_facts = [fact1]
            processed.add(fact1.fact_id)

            for fact2 in facts[i + 1:]:
                if fact2.fact_id in processed:
                    continue

                similarity = self._calculate_similarity(fact1.text, fact2.text)

                if similarity >= self.similarity_threshold:
                    similar_facts.append(fact2)
                    processed.add(fact2.fact_id)

            # Only create group if we found duplicates
            if len(similar_facts) > 1:
                # Calculate average similarity within group
                total_sim = 0.0
                comparisons = 0

                for j, f1 in enumerate(similar_facts):
                    for f2 in similar_facts[j + 1:]:
                        total_sim += self._calculate_similarity(f1.text, f2.text)
                        comparisons += 1

                avg_similarity = total_sim / max(comparisons, 1)

                # Select primary fact (highest importance)
                primary = self.select_primary_fact(similar_facts)

                duplicate_groups.append(DuplicateGroup(
                    facts=similar_facts,
                    similarity_score=avg_similarity,
                    primary_fact_id=primary.fact_id,
                    suggested_action="merge" if avg_similarity > 0.85 else "manual_review"
                ))

        return duplicate_groups

    def select_primary_fact(self, facts: List[Fact]) -> Fact:
        """
        Select the primary fact to keep (highest importance)

        Args:
            facts: List of duplicate facts

        Returns:
            Fact with highest importance
        """
        if not facts:
            raise ValueError("Cannot select primary from empty list")

        return max(facts, key=lambda f: f.importance)

    def merge_tags(self, facts: List[Fact]) -> List[str]:
        """
        Merge tags from all duplicate facts

        Args:
            facts: List of duplicate facts

        Returns:
            Combined list of unique tags
        """
        all_tags = set()

        for fact in facts:
            if fact.tags:
                all_tags.update(fact.tags)

        return list(all_tags)

    def sum_usage_counts(self, facts: List[Fact]) -> int:
        """
        Sum usage counts from all duplicate facts

        Args:
            facts: List of duplicate facts

        Returns:
            Total usage count
        """
        return sum(f.usage_count for f in facts)

    def create_merged_fact(self, facts: List[Fact]) -> Fact:
        """
        Create a merged fact from duplicates

        Keeps primary fact (highest importance) and:
        - Merges tags from all duplicates
        - Sums usage counts
        - Preserves highest importance

        Args:
            facts: List of duplicate facts

        Returns:
            New Fact with merged data
        """
        if not facts:
            raise ValueError("Cannot merge empty list of facts")

        # Get primary fact (highest importance)
        primary = self.select_primary_fact(facts)

        # Merge data from all duplicates
        merged_tags = self.merge_tags(facts)
        total_usage = self.sum_usage_counts(facts)

        # Create merged fact based on primary
        return Fact(
            fact_id=primary.fact_id,
            text=primary.text,
            importance=primary.importance,
            confidence=primary.confidence,
            tags=merged_tags,
            created=primary.created,
            updated=primary.updated,
            last_accessed=primary.last_accessed,
            fact_type=primary.fact_type,
            needs_update=primary.needs_update,
            update_frequency=primary.update_frequency,
            source=primary.source,
            source_session_id=primary.source_session_id,
            related_fact_ids=primary.related_fact_ids,
            context_maps=primary.context_maps,
            meta_data=primary.meta_data,
            usage_count=total_usage,
        )

    def get_facts_to_delete(self, facts: List[Fact], primary_id: str) -> List[str]:
        """
        Get list of fact IDs to delete after merge

        Args:
            facts: List of duplicate facts
            primary_id: ID of the primary fact to keep

        Returns:
            List of fact IDs to delete
        """
        return [f.fact_id for f in facts if f.fact_id != primary_id]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity between two strings

        Uses SequenceMatcher for fuzzy matching

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Normalize texts for comparison
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        return SequenceMatcher(None, t1, t2).ratio()