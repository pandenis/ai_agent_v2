"""
Tests for Analytics Dashboard.

Provides comprehensive analytics and metrics visualization
for the AI Agent orchestration system including:
- Query statistics
- Strategy distribution
- Cost analytics
- Performance metrics
- Time-series data

Test categories:
- Dashboard initialization
- Query analytics
- Strategy metrics
- Cost tracking
- Performance analysis
"""

import pytest
from app.services.orchestrator.analytics_dashboard import AnalyticsDashboard


class TestAnalyticsDashboard:
    """Tests for AnalyticsDashboard class."""

    def test_dashboard_creation(self):
        """Test: AnalyticsDashboard can be instantiated with dependencies."""
        # Arrange & Act
        dashboard = AnalyticsDashboard()

        # Assert
        assert dashboard is not None
        assert dashboard.metrics is not None
        assert dashboard.feedback_collector is not None

    def test_get_query_stats_empty(self):
        """Test: get_query_stats returns zeros when no data."""
        # Arrange
        dashboard = AnalyticsDashboard()

        # Act
        stats = dashboard.get_query_stats()

        # Assert
        assert stats["total_queries"] == 0
        assert stats["successful_queries"] == 0
        assert stats["failed_queries"] == 0
        assert stats["success_rate"] == 0.0

    def test_get_query_stats_with_data(self):
        """Test: get_query_stats returns correct statistics."""
        # Arrange
        from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
        
        metrics = OrchestratorMetrics()
        # Simulate some queries
        metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2500, cost_usd=0.001)
        metrics.track_query(strategy="direct", elapsed_time_ms=150, cost_usd=0.0)
        
        dashboard = AnalyticsDashboard(metrics=metrics)

        # Act
        stats = dashboard.get_query_stats()

        # Assert
        assert stats["total_queries"] == 3
        assert stats["successful_queries"] == 3
        assert stats["success_rate"] == 1.0

    def test_get_strategy_distribution_empty(self):
        """Test: get_strategy_distribution returns empty when no data."""
        # Arrange
        dashboard = AnalyticsDashboard()

        # Act
        distribution = dashboard.get_strategy_distribution()

        # Assert
        assert distribution["total"] == 0
        assert distribution["strategies"] == {}

    def test_get_strategy_distribution_with_data(self):
        """Test: get_strategy_distribution returns correct percentages."""
        # Arrange
        from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
        
        metrics = OrchestratorMetrics()
        # 5 direct, 3 enhanced, 2 deep_reasoning = 10 total
        for _ in range(5):
            metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        for _ in range(3):
            metrics.track_query(strategy="enhanced", elapsed_time_ms=2000, cost_usd=0.001)
        for _ in range(2):
            metrics.track_query(strategy="deep_reasoning", elapsed_time_ms=10000, cost_usd=0.005)
        
        dashboard = AnalyticsDashboard(metrics=metrics)

        # Act
        distribution = dashboard.get_strategy_distribution()

        # Assert
        assert distribution["total"] == 10
        assert distribution["strategies"]["direct"]["count"] == 5
        assert distribution["strategies"]["direct"]["percentage"] == pytest.approx(50.0)
        assert distribution["strategies"]["enhanced"]["count"] == 3
        assert distribution["strategies"]["enhanced"]["percentage"] == pytest.approx(30.0)
        assert distribution["strategies"]["deep_reasoning"]["count"] == 2
        assert distribution["strategies"]["deep_reasoning"]["percentage"] == pytest.approx(20.0)

    def test_get_cost_analytics_empty(self):
        """Test: get_cost_analytics returns zeros when no data."""
        # Arrange
        dashboard = AnalyticsDashboard()

        # Act
        costs = dashboard.get_cost_analytics()

        # Assert
        assert costs["total_cost_usd"] == 0.0
        assert costs["avg_cost_per_query"] == 0.0
        assert costs["cost_by_strategy"] == {}

    def test_get_cost_analytics_with_data(self):
        """Test: get_cost_analytics returns correct cost breakdown."""
        # Arrange
        from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
        
        metrics = OrchestratorMetrics()
        # direct: free, enhanced: $0.001 each, deep: $0.005 each
        metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2000, cost_usd=0.001)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2000, cost_usd=0.001)
        metrics.track_query(strategy="deep_reasoning", elapsed_time_ms=10000, cost_usd=0.005)
        
        dashboard = AnalyticsDashboard(metrics=metrics)

        # Act
        costs = dashboard.get_cost_analytics()

        # Assert
        # Total: 0 + 0 + 0.001 + 0.001 + 0.005 = 0.007
        assert costs["total_cost_usd"] == pytest.approx(0.007)
        assert costs["avg_cost_per_query"] == pytest.approx(0.0014)  # 0.007 / 5

    def test_get_performance_metrics_empty(self):
        """Test: get_performance_metrics returns zeros when no data."""
        # Arrange
        dashboard = AnalyticsDashboard()

        # Act
        perf = dashboard.get_performance_metrics()

        # Assert
        assert perf["avg_latency_ms"] == 0.0
        assert perf["total_queries"] == 0
        assert perf["latency_by_strategy"] == {}

    def test_get_performance_metrics_with_data(self):
        """Test: get_performance_metrics returns correct latency stats."""
        # Arrange
        from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
        
        metrics = OrchestratorMetrics()
        # direct: fast, enhanced: medium, deep: slow
        metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        metrics.track_query(strategy="direct", elapsed_time_ms=200, cost_usd=0.0)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2000, cost_usd=0.001)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=3000, cost_usd=0.001)
        metrics.track_query(strategy="deep_reasoning", elapsed_time_ms=15000, cost_usd=0.005)
        
        dashboard = AnalyticsDashboard(metrics=metrics)

        # Act
        perf = dashboard.get_performance_metrics()

        # Assert
        # Avg: (100+200+2000+3000+15000) / 5 = 4060ms
        assert perf["avg_latency_ms"] == pytest.approx(4060.0)
        assert perf["total_queries"] == 5

    def test_get_dashboard_summary(self):
        """Test: get_dashboard_summary returns comprehensive summary."""
        # Arrange
        from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
        from app.services.orchestrator.feedback_collector import FeedbackCollector
        
        metrics = OrchestratorMetrics()
        metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2000, cost_usd=0.001)
        metrics.track_query(strategy="deep_reasoning", elapsed_time_ms=10000, cost_usd=0.005)
        
        feedback = FeedbackCollector()
        feedback.add_feedback(response_id="q1", rating=5, strategy="direct", thumbs_up=True)
        feedback.add_feedback(response_id="q2", rating=4, strategy="enhanced", thumbs_up=True)
        
        dashboard = AnalyticsDashboard(metrics=metrics, feedback_collector=feedback)

        # Act
        summary = dashboard.get_dashboard_summary()

        # Assert
        assert "query_stats" in summary
        assert "strategy_distribution" in summary
        assert "cost_analytics" in summary
        assert "performance_metrics" in summary
        assert "user_satisfaction" in summary
        
        assert summary["query_stats"]["total_queries"] == 3
        assert summary["user_satisfaction"]["total_feedbacks"] == 2
