"""
Tests for ReasoningPlanner - Multi-step reasoning for complex queries
"""
import pytest
from app.services.orchestrator.reasoning_planner import (
    ReasoningPlanner,
    ReasoningPlan,
    ReasoningStep
)
from app.services.orchestrator.query_analyzer import QueryAnalysis
from app.services.orchestrator.memory_evaluator import MemoryEvaluation


class TestReasoningPlanner:
    """Tests for multi-step reasoning planning"""

    def test_planner_exists(self):
        """Test: ReasoningPlanner class can be instantiated"""
        planner = ReasoningPlanner()
        assert planner is not None

    def test_create_plan_returns_reasoning_plan(self):
        """Test: create_plan returns a ReasoningPlan object"""
        planner = ReasoningPlanner()
        query_analysis = QueryAnalysis(
            complexity="complex",
            intent="question",
            query_type="reasoning",
            entities=["Mediterranean", "heart health"],
            topics=["medical", "nutrition"],
            requires_memory=True,
            requires_reasoning=True,
            confidence=0.7
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.3,
            relevant_facts=[],
            gaps=["diet research"],
            confidence=0.5
        )

        plan = planner.create_plan(
            query="Compare Mediterranean diet with keto for heart health",
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )

        assert isinstance(plan, ReasoningPlan)
        assert len(plan.steps) > 0

    def test_plan_has_ordered_steps(self):
        """Test: Plan steps have sequential step numbers"""
        planner = ReasoningPlanner()
        query_analysis = QueryAnalysis(
            complexity="complex",
            intent="question",
            query_type="reasoning",
            entities=["Tokyo", "Paris"],
            topics=["travel", "culture"],
            requires_memory=True,
            requires_reasoning=True,
            confidence=0.7
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.4,
            relevant_facts=[{"text": "User visited Japan last year"}],
            gaps=["Paris details"],
            confidence=0.6
        )

        plan = planner.create_plan(
            query="Compare living costs between Tokyo and Paris",
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )

        # Check steps are numbered sequentially
        for i, step in enumerate(plan.steps):
            assert step.step_number == i + 1

    def test_plan_includes_memory_step_when_facts_exist(self):
        """Test: Plan includes memory search when relevant facts exist"""
        planner = ReasoningPlanner()
        query_analysis = QueryAnalysis(
            complexity="complex",
            intent="question",
            query_type="reasoning",
            entities=["Italian cuisine"],
            topics=["cooking"],
            requires_memory=True,
            requires_reasoning=True,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.6,
            relevant_facts=[
                {"text": "User loves pasta and Italian food", "importance": 0.9}
            ],
            gaps=[],
            confidence=0.8
        )

        plan = planner.create_plan(
            query="What authentic Italian dishes should I try cooking at home?",
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )

        # Should have a step that uses memory
        actions = [step.action for step in plan.steps]
        assert "gather_context" in actions or "search_memory" in actions

    def test_plan_includes_analysis_step(self):
        """Test: Complex queries always include an analysis step"""
        planner = ReasoningPlanner()
        query_analysis = QueryAnalysis(
            complexity="complex",
            intent="question",
            query_type="reasoning",
            entities=["electric cars", "gasoline cars"],
            topics=["automotive", "environment"],
            requires_memory=True,
            requires_reasoning=True,
            confidence=0.7
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.2,
            relevant_facts=[],
            gaps=["environmental impact data"],
            confidence=0.5
        )

        plan = planner.create_plan(
            query="What are the pros and cons of electric vs gasoline cars?",
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )

        actions = [step.action for step in plan.steps]
        assert "analyze" in actions

    def test_plan_ends_with_synthesize(self):
        """Test: Plan always ends with synthesis step"""
        planner = ReasoningPlanner()
        query_analysis = QueryAnalysis(
            complexity="complex",
            intent="question",
            query_type="reasoning",
            entities=["climate change", "economy"],
            topics=["environment", "economics"],
            requires_memory=True,
            requires_reasoning=True,
            confidence=0.7
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.3,
            relevant_facts=[],
            gaps=["economic projections"],
            confidence=0.5
        )

        plan = planner.create_plan(
            query="How will climate change affect the global economy?",
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )

        # Last step should be synthesize
        assert plan.steps[-1].action == "synthesize"