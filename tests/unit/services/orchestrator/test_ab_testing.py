"""
Tests for A/B Testing Framework

TDD approach for implementing A/B testing functionality:
1. Experiment configuration
2. Traffic splitting
3. Results collection
4. Statistical analysis
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime


# ==========================================
# Test 1: ABTestingManager exists and is importable
# ==========================================

def test_ab_testing_manager_is_importable():
    """
    Test: ABTestingManager can be imported

    Expected: Import succeeds
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    assert ABTestingManager is not None


# ==========================================
# Test 2: Can create experiment
# ==========================================

def test_create_experiment():
    """
    Test: Can create a new A/B experiment

    Expected: Experiment is created with name and variants
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()

    experiment = manager.create_experiment(
        name="strategy_comparison",
        variants=["direct", "enhanced"],
        traffic_split=[0.5, 0.5]  # 50/50 split
    )

    assert experiment is not None
    assert experiment.name == "strategy_comparison"
    assert len(experiment.variants) == 2
    assert experiment.is_active == True


# ==========================================
# Test 3: Get variant for user (deterministic)
# ==========================================

def test_get_variant_deterministic():
    """
    Test: Same user always gets same variant

    Expected: Consistent assignment based on user_id
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()
    manager.create_experiment(
        name="test_exp",
        variants=["A", "B"],
        traffic_split=[0.5, 0.5]
    )

    # Same user should always get same variant
    variant1 = manager.get_variant("test_exp", user_id="user123")
    variant2 = manager.get_variant("test_exp", user_id="user123")

    assert variant1 == variant2


# ==========================================
# Test 4: Traffic split works correctly
# ==========================================

def test_traffic_split_distribution():
    """
    Test: Traffic is split according to configuration

    Expected: ~50/50 distribution over many users
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()
    manager.create_experiment(
        name="split_test",
        variants=["A", "B"],
        traffic_split=[0.5, 0.5]
    )

    # Test with many users
    results = {"A": 0, "B": 0}
    for i in range(1000):
        variant = manager.get_variant("split_test", user_id=f"user_{i}")
        results[variant] += 1

    # Should be roughly 50/50 (allow 10% tolerance)
    assert 400 <= results["A"] <= 600
    assert 400 <= results["B"] <= 600


# ==========================================
# Test 5: Record experiment result
# ==========================================

def test_record_result():
    """
    Test: Can record result for an experiment

    Expected: Result is stored with variant and metrics
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()
    manager.create_experiment(
        name="result_test",
        variants=["A", "B"],
        traffic_split=[0.5, 0.5]
    )

    # Record some results
    manager.record_result(
        experiment_name="result_test",
        variant="A",
        user_id="user1",
        success=True,
        response_time_ms=100.0
    )

    manager.record_result(
        experiment_name="result_test",
        variant="B",
        user_id="user2",
        success=True,
        response_time_ms=150.0
    )

    stats = manager.get_experiment_stats("result_test")

    assert stats["total_participants"] == 2
    assert "A" in stats["variants"]
    assert "B" in stats["variants"]


# ==========================================
# Test 6: Get experiment statistics
# ==========================================

def test_get_experiment_stats():
    """
    Test: Can get statistics for experiment

    Expected: Stats include success rate, avg response time per variant
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()
    manager.create_experiment(
        name="stats_test",
        variants=["control", "treatment"],
        traffic_split=[0.5, 0.5]
    )

    # Record results for control (slower, less successful)
    for i in range(10):
        manager.record_result(
            experiment_name="stats_test",
            variant="control",
            user_id=f"control_{i}",
            success=(i < 7),  # 70% success
            response_time_ms=200.0
        )

    # Record results for treatment (faster, more successful)
    for i in range(10):
        manager.record_result(
            experiment_name="stats_test",
            variant="treatment",
            user_id=f"treatment_{i}",
            success=(i < 9),  # 90% success
            response_time_ms=100.0
        )

    stats = manager.get_experiment_stats("stats_test")

    assert stats["variants"]["control"]["success_rate"] == 0.7
    assert stats["variants"]["treatment"]["success_rate"] == 0.9
    assert stats["variants"]["control"]["avg_response_time_ms"] == 200.0
    assert stats["variants"]["treatment"]["avg_response_time_ms"] == 100.0


# ==========================================
# Test 7: Determine winner
# ==========================================

def test_get_winner():
    """
    Test: Can determine winning variant

    Expected: Returns variant with best success rate
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()
    manager.create_experiment(
        name="winner_test",
        variants=["old", "new"],
        traffic_split=[0.5, 0.5]
    )

    # Old version: 60% success
    for i in range(10):
        manager.record_result(
            experiment_name="winner_test",
            variant="old",
            user_id=f"old_{i}",
            success=(i < 6),
            response_time_ms=150.0
        )

    # New version: 80% success
    for i in range(10):
        manager.record_result(
            experiment_name="winner_test",
            variant="new",
            user_id=f"new_{i}",
            success=(i < 8),
            response_time_ms=120.0
        )

    winner = manager.get_winner("winner_test")

    assert winner["variant"] == "new"
    assert winner["success_rate"] == 0.8
    assert winner["improvement"] == pytest.approx(0.333, rel=0.1)  # 33% improvement


# ==========================================
# Test 8: Deactivate experiment
# ==========================================

def test_deactivate_experiment():
    """
    Test: Can deactivate an experiment

    Expected: Experiment no longer assigns variants
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()
    manager.create_experiment(
        name="deactivate_test",
        variants=["A", "B"],
        traffic_split=[0.5, 0.5]
    )

    # Should work while active
    variant = manager.get_variant("deactivate_test", user_id="user1")
    assert variant in ["A", "B"]

    # Deactivate
    manager.deactivate_experiment("deactivate_test")

    # Should return None when inactive
    variant = manager.get_variant("deactivate_test", user_id="user2")
    assert variant is None


# ==========================================
# Test 9: List active experiments
# ==========================================

def test_list_experiments():
    """
    Test: Can list all experiments

    Expected: Returns list of experiment names and statuses
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()

    manager.create_experiment("exp1", ["A", "B"], [0.5, 0.5])
    manager.create_experiment("exp2", ["X", "Y", "Z"], [0.33, 0.33, 0.34])
    manager.deactivate_experiment("exp1")

    experiments = manager.list_experiments()

    assert len(experiments) == 2
    assert any(e["name"] == "exp1" and e["is_active"] == False for e in experiments)
    assert any(e["name"] == "exp2" and e["is_active"] == True for e in experiments)


# ==========================================
# Test 10: Invalid experiment returns None
# ==========================================

def test_invalid_experiment_returns_none():
    """
    Test: Getting variant for non-existent experiment returns None

    Expected: Returns None, no error
    """
    from app.services.orchestrator.ab_testing import ABTestingManager

    manager = ABTestingManager()

    variant = manager.get_variant("non_existent", user_id="user1")

    assert variant is None