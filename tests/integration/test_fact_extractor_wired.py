"""
Regression guard: fact_extractor must be injected into IntelligentOrchestrator.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.api.deps import get_orchestrator
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.mark.asyncio
async def test_get_orchestrator_injects_fact_extractor():
    """Verify get_orchestrator() injects a FactExtractor instance.
    Without this, _extract_and_save_facts() silently returns immediately
    and no facts are ever persisted. Regression guard for the missing
    fact_extractor injection bug."""
    db = AsyncMock()

    orchestrator = await get_orchestrator(db)

    assert isinstance(orchestrator, IntelligentOrchestrator)
    assert orchestrator.fact_extractor is not None
