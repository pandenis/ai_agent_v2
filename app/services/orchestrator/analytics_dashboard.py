"""
Analytics Dashboard for AI Agent Orchestration System.

Provides comprehensive analytics and metrics visualization including:
- Query statistics (total, by strategy, by time period)
- Strategy distribution and effectiveness
- Cost tracking and optimization insights
- Performance metrics (latency, success rate)
- Time-series data for trend analysis

Usage:
    >>> dashboard = AnalyticsDashboard()
    >>> summary = dashboard.get_dashboard_summary()
    >>> print(f"Total queries: {summary['total_queries']}")
    >>> print(f"Success rate: {summary['success_rate']:.1%}")
    
    >>> # Get detailed analytics
    >>> strategy_dist = dashboard.get_strategy_distribution()
    >>> cost_analytics = dashboard.get_cost_analytics()
    >>> performance = dashboard.get_performance_metrics()
"""

from typing import Dict, Any, List, Optional
from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
from app.services.orchestrator.feedback_collector import FeedbackCollector


class AnalyticsDashboard:
    """Comprehensive analytics dashboard for the orchestration system."""
    
    def __init__(
        self,
        metrics: Optional[OrchestratorMetrics] = None,
        feedback_collector: Optional[FeedbackCollector] = None
    ):
        """Initialize dashboard with metrics and feedback sources.
        
        Args:
            metrics: OrchestratorMetrics instance (created if not provided)
            feedback_collector: FeedbackCollector instance (created if not provided)
        """
        self.metrics = metrics or OrchestratorMetrics()
        self.feedback_collector = feedback_collector or FeedbackCollector()
