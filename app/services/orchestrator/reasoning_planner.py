"""
ReasoningPlanner - Multi-step reasoning for complex queries.

Breaks down complex questions into executable steps:
1. Gather context from memory
2. Analyze the problem
3. Synthesize final answer

Usage:
    >>> planner = ReasoningPlanner()
    >>> plan = planner.create_plan(query, query_analysis, memory_eval)
    >>> for step in plan.steps:
    ...     print(f"Step {step.step_number}: {step.action}")
"""
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.orchestrator.query_analyzer import QueryAnalysis
from app.services.orchestrator.memory_evaluator import MemoryEvaluation


@dataclass
class ReasoningStep:
    """Single step in a reasoning plan"""
    step_number: int
    action: str  # "gather_context", "search_memory", "analyze", "synthesize"
    description: str
    tool: Optional[str] = None  # "memory", "web_search", "document_search"


@dataclass
class ReasoningPlan:
    """Complete plan for multi-step reasoning"""
    query: str
    steps: List[ReasoningStep] = field(default_factory=list)
    estimated_time: float = 0.0  # seconds
    estimated_cost: float = 0.0  # USD


class ReasoningPlanner:
    """Plans multi-step reasoning for complex queries"""

    def create_plan(
            self,
            query: str,
            query_analysis: QueryAnalysis,
            memory_eval: MemoryEvaluation
    ) -> ReasoningPlan:
        """
        Create a reasoning plan for a complex query.

        Args:
            query: The user's question
            query_analysis: Analysis of query complexity/intent
            memory_eval: Evaluation of memory coverage

        Returns:
            ReasoningPlan with ordered steps
        """
        steps = []
        step_number = 1

        # Step 1: Gather context from memory (if facts exist)
        if memory_eval.relevant_facts:
            steps.append(ReasoningStep(
                step_number=step_number,
                action="gather_context",
                description="Gather relevant context from memory",
                tool="memory"
            ))
            step_number += 1

        # Step 2: Web search (if memory has gaps)
        if memory_eval.gaps:
            gaps_text = ", ".join(memory_eval.gaps[:3])  # Top 3 gaps
            steps.append(ReasoningStep(
                step_number=step_number,
                action="web_search",
                description=f"Search for: {gaps_text}",
                tool="web_search"
            ))
            step_number += 1

        # Step 3: Analyze the problem
        steps.append(ReasoningStep(
            step_number=step_number,
            action="analyze",
            description=f"Analyze: {query[:50]}...",
            tool=None
        ))
        step_number += 1

        # Step 4: Synthesize final answer (always last)
        steps.append(ReasoningStep(
            step_number=step_number,
            action="synthesize",
            description="Synthesize comprehensive answer",
            tool=None
        ))

        return ReasoningPlan(
            query=query,
            steps=steps,
            estimated_time=15.0,  # Deep reasoning ~15s
            estimated_cost=0.005  # ~$0.005
        )