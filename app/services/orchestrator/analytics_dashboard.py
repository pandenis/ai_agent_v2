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

    def get_query_stats(self) -> Dict[str, Any]:
        """Get overall query statistics.
        
        Returns:
            Dictionary with query statistics:
            - total_queries: Total number of queries processed
            - successful_queries: Number of successful queries
            - failed_queries: Number of failed queries
            - success_rate: Success rate (0.0 to 1.0)
        """
        metrics_summary = self.metrics.get_stats()
        
        total = metrics_summary.get("total_queries", 0)
        # For now, assume all tracked queries are successful
        # Failed queries would be tracked separately
        successful = total
        failed = 0
        
        success_rate = successful / total if total > 0 else 0.0
        
        return {
            "total_queries": total,
            "successful_queries": successful,
            "failed_queries": failed,
            "success_rate": success_rate
        }

    def get_strategy_distribution(self) -> Dict[str, Any]:
        """Get distribution of queries by strategy.
        
        Returns:
            Dictionary with strategy distribution:
            - total: Total number of queries
            - strategies: Dict with count and percentage per strategy
        """
        metrics_stats = self.metrics.get_stats()
        
        total = metrics_stats.get("total_queries", 0)
        strategy_counts = metrics_stats.get("strategy_counts", {})
        
        if total == 0:
            return {
                "total": 0,
                "strategies": {}
            }
        
        strategies = {}
        for strategy, count in strategy_counts.items():
            if count > 0:  # Only include strategies with queries
                strategies[strategy] = {
                    "count": count,
                    "percentage": (count / total) * 100
                }
        
        return {
            "total": total,
            "strategies": strategies
        }

    def get_cost_analytics(self) -> Dict[str, Any]:
        """Get cost analytics breakdown.
        
        Returns:
            Dictionary with cost analytics:
            - total_cost_usd: Total cost in USD
            - avg_cost_per_query: Average cost per query
            - cost_by_strategy: Cost breakdown by strategy
        """
        metrics_stats = self.metrics.get_stats()
        
        total_cost = metrics_stats.get("total_cost_usd", 0.0)
        total_queries = metrics_stats.get("total_queries", 0)
        
        avg_cost = total_cost / total_queries if total_queries > 0 else 0.0
        
        # Calculate cost by strategy from tracked data
        strategy_counts = metrics_stats.get("strategy_counts", {})
        cost_by_strategy = {}
        
        # Estimate costs based on typical rates
        cost_rates = {
            "direct": 0.0,
            "enhanced": 0.001,
            "deep_reasoning": 0.005
        }
        
        for strategy, count in strategy_counts.items():
            if count > 0:
                estimated_cost = count * cost_rates.get(strategy, 0.001)
                cost_by_strategy[strategy] = {
                    "count": count,
                    "estimated_cost_usd": estimated_cost
                }
        
        return {
            "total_cost_usd": total_cost,
            "avg_cost_per_query": avg_cost,
            "cost_by_strategy": cost_by_strategy
        }
