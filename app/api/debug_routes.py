"""Debug endpoints for inspecting internal memory state."""

from fastapi import APIRouter, Depends

from app.api.deps import get_orchestrator
from app.schemas.debug import (
    EnrichedGraphStats,
    MemoryDebugResponse,
    MemoryEdgeDebug,
    MemoryMetricsResponse,
    MemoryNodeDebug,
    RetrievalLogDebug,
    WriteLogDebug,
)
from app.services.orchestrator.orchestrator import IntelligentOrchestrator

debug_router = APIRouter()


@debug_router.get(
    "/debug/memory/metrics",
    response_model=MemoryMetricsResponse,
    summary="Get aggregate memory operation metrics",
    description="Returns cumulative stats on memory retrievals and writes.",
)
async def get_memory_metrics(
    orchestrator: IntelligentOrchestrator = Depends(get_orchestrator),
) -> MemoryMetricsResponse:
    """Return cumulative metrics across all memory operations.

    If no MemoryMap is attached, returns a zeroed response.
    """
    memory_map = orchestrator.memory_map

    if memory_map is None:
        return MemoryMetricsResponse(
            total_retrievals=0,
            total_writes=0,
            total_nodes_scored=0,
            total_nodes_returned=0,
            avg_retrieval_ms=0.0,
            avg_nodes_returned=0.0,
            total_write_ops_by_type={"add_node": 0, "add_edge": 0, "remove_node": 0},
            total_dedup_detections=0,
        )

    return MemoryMetricsResponse(**memory_map.metrics.get_summary())


@debug_router.get(
    "/debug/memory/{session_id}",
    response_model=MemoryDebugResponse,
    summary="Inspect memory map for a session",
    description="Returns nodes, edges, and stats for the memory map. Debug only.",
)
async def get_memory_debug(
    session_id: str,
    orchestrator: IntelligentOrchestrator = Depends(get_orchestrator),
) -> MemoryDebugResponse:
    """Return the current in-memory graph state for observability.

    If no MemoryMap is attached to the orchestrator, returns an empty response
    with zero counts rather than a 404.
    """
    memory_map = orchestrator.memory_map

    if memory_map is None:
        return MemoryDebugResponse(
            session_id=session_id,
            graph_stats=EnrichedGraphStats(
                node_count=0, edge_count=0,
                avg_importance=0.0, avg_weight=0.0,
            ),
            nodes=[],
            edges=[],
        )

    nodes = [
        MemoryNodeDebug(
            id=node.id,
            content=node.content,
            node_type=node.node_type,
            importance=node.importance,
            access_count=node.access_count,
            weight=node.calculate_weight(),
        )
        for node in memory_map.nodes.values()
    ]

    edges = [
        MemoryEdgeDebug(
            source_id=edge.source_id,
            target_id=edge.target_id,
            edge_type=edge.edge_type,
            weight=edge.weight,
        )
        for edge in memory_map.edges
    ]

    # Compute enriched stats
    if memory_map.node_count > 0:
        all_nodes = list(memory_map.nodes.values())
        avg_importance = sum(n.importance for n in all_nodes) / len(all_nodes)
        avg_weight = sum(n.calculate_weight() for n in all_nodes) / len(all_nodes)
    else:
        avg_importance = 0.0
        avg_weight = 0.0

    # Serialize recent retrieval logs
    recent_retrievals = [
        RetrievalLogDebug(
            query=log.query,
            nodes_scored=log.nodes_scored,
            nodes_returned=log.nodes_returned,
            nodes_dropped=log.nodes_dropped,
            tokens_used=log.tokens_used,
            elapsed_ms=log.elapsed_ms,
            timestamp=log.timestamp.isoformat(),
        )
        for log in memory_map.get_retrieval_history(last_n=5)
    ]

    # Serialize recent write logs
    recent_writes = [
        WriteLogDebug(
            operation=log.operation,
            node_id=log.node_id,
            target_id=log.target_id,
            edge_type=log.edge_type,
            dedup_detected=log.dedup_detected,
            success=log.success,
            timestamp=log.timestamp.isoformat(),
        )
        for log in memory_map.get_write_history(last_n=5)
    ]

    return MemoryDebugResponse(
        session_id=session_id,
        graph_stats=EnrichedGraphStats(
            node_count=memory_map.node_count,
            edge_count=memory_map.edge_count,
            avg_importance=avg_importance,
            avg_weight=avg_weight,
        ),
        nodes=nodes,
        edges=edges,
        recent_retrievals=recent_retrievals,
        recent_writes=recent_writes,
    )
