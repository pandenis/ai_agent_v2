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

import logging
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
import re

from app.models.memory_v2 import Fact

if TYPE_CHECKING:
    from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    """Result of deduplication operation"""
    groups_found: int
    facts_merged: int
    facts_deleted: int
    errors: List[str] = field(default_factory=list)


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

    def __init__(self, similarity_threshold: float = 0.80):
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

    import re

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0.0-1.0
        """
        # Normalize: lowercase and remove punctuation
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())

        # Tokenize
        words1 = set(text1_clean.split())
        words2 = set(text2_clean.split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    async def deduplicate_all(
        self,
        memory_service: "MemoryService",
        dry_run: bool = False
    ) -> DeduplicationResult:
        """
        Find and merge all duplicate facts in the database

        Args:
            memory_service: MemoryService instance for database access
            dry_run: If True, only report duplicates without deleting

        Returns:
            DeduplicationResult with statistics
        """
        result = DeduplicationResult(
            groups_found=0,
            facts_merged=0,
            facts_deleted=0,
            errors=[]
        )

        try:
            # Get all facts from database
            all_facts_models = await memory_service.get_facts(
                min_importance=0.0,
                limit=10000
            )

            # Convert to Fact dataclass for processing
            all_facts = [fm.to_dataclass() for fm in all_facts_models]

            logger.info(f"Analyzing {len(all_facts)} facts for duplicates...")

            # Find duplicate groups
            duplicate_groups = self.find_duplicates(all_facts)
            result.groups_found = len(duplicate_groups)

            if not duplicate_groups:
                logger.info("No duplicates found")
                return result

            logger.info(f"Found {len(duplicate_groups)} duplicate groups")

            if dry_run:
                # Just count what would be deleted
                for group in duplicate_groups:
                    result.facts_deleted += len(group.facts) - 1
                return result

            # Process each duplicate group
            for group in duplicate_groups:
                try:
                    # Create merged fact
                    merged = self.create_merged_fact(group.facts)

                    # Get facts to delete
                    to_delete = self.get_facts_to_delete(group.facts, merged.fact_id)

                    # Update primary fact with merged data
                    await memory_service.update_fact(
                        fact_id=merged.fact_id,
                        tags=merged.tags,
                        usage_count=merged.usage_count
                    )

                    # Delete duplicates
                    for fact_id in to_delete:
                        await memory_service.delete_fact(fact_id)
                        result.facts_deleted += 1

                    result.facts_merged += 1
                    logger.debug(f"Merged group: kept {merged.fact_id}, deleted {len(to_delete)}")

                except Exception as e:
                    error_msg = f"Error processing group {group.primary_fact_id}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

            logger.info(
                f"Deduplication complete: {result.facts_merged} merged, "
                f"{result.facts_deleted} deleted, {len(result.errors)} errors"
            )

        except Exception as e:
            error_msg = f"Deduplication failed: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        return result