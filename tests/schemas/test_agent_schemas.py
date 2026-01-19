"""Tests for agent schemas including QueryAnalysisResponse"""

import pytest
from app.schemas.agent import QueryAnalysisResponse, OrchestrateResponse, OrchestratorMetadata


class TestQueryAnalysisResponse:
    """Tests for QueryAnalysisResponse schema"""

    def test_query_analysis_response_creation(self):
        """Test: QueryAnalysisResponse can be created with all fields"""
        # Arrange
        data = {
            "complexity": "simple",
            "intent": "question",
            "topics": ["name", "personal"],
            "entities": ["Denis"],
            "query_type": "personal_query",
            "confidence": 0.85
        }
        
        # Act
        analysis = QueryAnalysisResponse(**data)
        
        # Assert
        assert analysis.complexity == "simple"
        assert analysis.intent == "question"
        assert analysis.topics == ["name", "personal"]
        assert analysis.entities == ["Denis"]
        assert analysis.query_type == "personal_query"
        assert analysis.confidence == 0.85

    def test_query_analysis_in_orchestrate_response(self):
        """Test: OrchestrateResponse includes query_analysis field"""
        # Arrange
        query_analysis = QueryAnalysisResponse(
            complexity="medium",
            intent="question",
            topics=["weather"],
            entities=[],
            query_type="factual_query",
            confidence=0.9
        )
        metadata = OrchestratorMetadata(
            strategy="direct",
            confidence=0.8,
            sources=["memory"],
            elapsed_time_ms=15.5,
            cost_usd=0.0,
            cached=False,
            memory_coverage=0.75
        )
        
        # Act
        response = OrchestrateResponse(
            text="The weather is sunny",
            metadata=metadata,
            query_analysis=query_analysis
        )
        
        # Assert
        assert response.query_analysis is not None
        assert response.query_analysis.complexity == "medium"
        assert response.query_analysis.topics == ["weather"]
