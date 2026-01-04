"""
Tests for get_orchestrator() FastAPI dependency

TDD Step 1: Test that get_orchestrator() dependency exists and works correctly.

These tests verify:
1. get_orchestrator() function exists in deps.py
2. It returns an IntelligentOrchestrator instance
3. All required services are properly injected
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession


# ==========================================
# Test 1: Dependency exists and is importable
# ==========================================

def test_get_orchestrator_is_importable():
    """
    Test: get_orchestrator can be imported from deps module

    Expected: Import succeeds without error
    """
    from app.api.deps import get_orchestrator

    assert get_orchestrator is not None
    assert callable(get_orchestrator)


# ==========================================
# Test 2: Dependency returns IntelligentOrchestrator
# ==========================================

@pytest.mark.asyncio
async def test_get_orchestrator_returns_orchestrator_instance():
    """
    Test: get_orchestrator returns an IntelligentOrchestrator instance

    Expected: Return type is IntelligentOrchestrator
    """
    from app.api.deps import get_orchestrator
    from app.services.orchestrator.orchestrator import IntelligentOrchestrator

    # Create mock db session
    mock_db = AsyncMock(spec=AsyncSession)

    # Call the dependency
    orchestrator = await get_orchestrator(db=mock_db)

    # Verify it's an IntelligentOrchestrator
    assert isinstance(orchestrator, IntelligentOrchestrator)


# ==========================================
# Test 3: Orchestrator has required services
# ==========================================

@pytest.mark.asyncio
async def test_orchestrator_has_memory_service():
    """
    Test: Orchestrator has memory_service injected

    Expected: orchestrator.memory_service is not None
    """
    from app.api.deps import get_orchestrator

    mock_db = AsyncMock(spec=AsyncSession)
    orchestrator = await get_orchestrator(db=mock_db)

    assert orchestrator.memory_service is not None


@pytest.mark.asyncio
async def test_orchestrator_has_agent_registry():
    """
    Test: Orchestrator has agent_registry injected

    Expected: orchestrator.agent_registry is not None
    """
    from app.api.deps import get_orchestrator

    mock_db = AsyncMock(spec=AsyncSession)
    orchestrator = await get_orchestrator(db=mock_db)

    assert orchestrator.agent_registry is not None


@pytest.mark.asyncio
async def test_orchestrator_has_web_search_service():
    """
    Test: Orchestrator has web_search_service injected

    Expected: orchestrator.web_search_service is not None
    """
    from app.api.deps import get_orchestrator

    mock_db = AsyncMock(spec=AsyncSession)
    orchestrator = await get_orchestrator(db=mock_db)

    assert orchestrator.web_search_service is not None


# ==========================================
# Test 4: Orchestrator has all components initialized
# ==========================================

@pytest.mark.asyncio
async def test_orchestrator_has_core_components():
    """
    Test: Orchestrator has all core components initialized

    Expected: All internal components exist
    """
    from app.api.deps import get_orchestrator

    mock_db = AsyncMock(spec=AsyncSession)
    orchestrator = await get_orchestrator(db=mock_db)

    # Core components
    assert orchestrator.query_analyzer is not None
    assert orchestrator.memory_evaluator is not None
    assert orchestrator.decision_engine is not None
    assert orchestrator.response_formatter is not None
    assert orchestrator.response_cache is not None


@pytest.mark.asyncio
async def test_orchestrator_has_chain_components():
    """
    Test: Orchestrator has chain execution components

    Expected: ChainBuilder and ChainExecutor exist
    """
    from app.api.deps import get_orchestrator

    mock_db = AsyncMock(spec=AsyncSession)
    orchestrator = await get_orchestrator(db=mock_db)

    # Chain components
    assert orchestrator.chain_builder is not None
    assert orchestrator.chain_executor is not None