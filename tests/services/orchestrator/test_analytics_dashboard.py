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
