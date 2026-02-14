import logging
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_log import MemoryRetrievalLog, MemoryWriteLog
from app.services.memory.memory_metrics import MemoryMetrics
from app.services.memory.memory_node import MemoryNode

logger = logging.getLogger(__name__)

_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "what", "where", "who",
    "how", "does", "do", "tell", "me", "about", "user", "my", "in", "to",
    "of", "and", "for",
})


class MemoryMap:
    """A graph-based memory map storing nodes and directed edges between them."""

    def __init__(self):
        """Initialize an empty memory map."""
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: List[MemoryEdge] = []
        self.last_retrieval_log: Optional[MemoryRetrievalLog] = None
        self.retrieval_history: List[MemoryRetrievalLog] = []
        self.write_history: List[MemoryWriteLog] = []
        self.metrics = MemoryMetrics()

    def add_node(self, node: MemoryNode) -> None:
        """Add a memory node to the map, indexed by its id.

        If a node with the same id already exists, the add is rejected and
        a dedup warning is logged.
        """
        if node.id in self.nodes:
            log = MemoryWriteLog(
                operation="add_node", node_id=node.id,
                dedup_detected=True, success=False, reason="duplicate node ID",
            )
            self.write_history.append(log)
            self.metrics.record_write(log)
            logger.warning(f"Memory write rejected: {log}")
            return
        self.nodes[node.id] = node
        log = MemoryWriteLog(operation="add_node", node_id=node.id, success=True)
        self.write_history.append(log)
        self.metrics.record_write(log)
        logger.info(f"Memory write: {log}")

    def add_edge(self, edge: MemoryEdge) -> None:
        """Add a directed edge between two existing nodes.

        Raises ValueError if source or target node does not exist.
        """
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node '{edge.source_id}' not found")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node '{edge.target_id}' not found")
        self.edges.append(edge)
        log = MemoryWriteLog(
            operation="add_edge", node_id=edge.source_id,
            target_id=edge.target_id, edge_type=edge.edge_type, success=True,
        )
        self.write_history.append(log)
        self.metrics.record_write(log)
        logger.info(f"Memory write: {log}")

    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Return the node with the given id, or None if not found."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[MemoryNode]:
        """Return all nodes connected by outgoing edges from the given node."""
        return [
            self.nodes[edge.target_id]
            for edge in self.edges
            if edge.source_id == node_id
        ]

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the map."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Return the number of edges in the map."""
        return len(self.edges)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all edges connected to it.

        Raises KeyError if the node does not exist.
        """
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' not found")
        del self.nodes[node_id]
        self.edges = [
            edge for edge in self.edges
            if edge.source_id != node_id and edge.target_id != node_id
        ]
        log = MemoryWriteLog(operation="remove_node", node_id=node_id, success=True)
        self.write_history.append(log)
        self.metrics.record_write(log)
        logger.info(f"Memory write: {log}")

    def __repr__(self) -> str:
        return f"MemoryMap({self.node_count} nodes, {self.edge_count} edges)"

    def get_retrieval_history(self, last_n: Optional[int] = None) -> List[MemoryRetrievalLog]:
        """Return retrieval history, optionally limited to the last N entries."""
        if last_n is None:
            return list(self.retrieval_history)
        return self.retrieval_history[-last_n:]

    def get_write_history(self, last_n: Optional[int] = None) -> List[MemoryWriteLog]:
        """Return write history, optionally limited to the last N entries."""
        if last_n is None:
            return list(self.write_history)
        return self.write_history[-last_n:]

    def build_local_slice(self, start_node_id: str, token_budget: int) -> 'MemoryMap':
        """Extract a subgraph around start_node_id within a token budget.

        Uses BFS up to 2 hops, prioritizing neighbors by edge weight descending.
        Token cost per node is estimated as len(node.content) // 4.
        The start node is always included. Edges between included nodes are copied.
        Returns an empty MemoryMap if start_node_id is not found.
        """
        slice_map = MemoryMap()
        if start_node_id not in self.nodes:
            return slice_map

        start_node = self.nodes[start_node_id]
        remaining_budget = token_budget - len(start_node.content) // 4
        slice_map.add_node(start_node)

        included: Set[str] = {start_node_id}
        # BFS queue holds (node_id, current_depth)
        queue: deque = deque([(start_node_id, 0)])

        while queue:
            current_id, depth = queue.popleft()
            if depth >= 2:
                continue
            for neighbor, _weight in self.find_related(current_id):
                if neighbor.id in included:
                    continue
                token_cost = len(neighbor.content) // 4
                if token_cost <= remaining_budget:
                    slice_map.add_node(neighbor)
                    included.add(neighbor.id)
                    remaining_budget -= token_cost
                    queue.append((neighbor.id, depth + 1))

        # Add all edges from original graph where both endpoints are included
        for edge in self.edges:
            if edge.source_id in included and edge.target_id in included:
                slice_map.edges.append(edge)

        return slice_map

    def to_prompt_context(self, max_tokens: Optional[int] = None) -> str:
        """Convert the memory map into a formatted string for LLM prompt injection.

        Nodes are sorted by calculate_weight() descending. Each node is rendered as
        a bullet with its type and content. Outgoing edges are shown as indented
        relationship lines. If max_tokens is provided, stops adding nodes when the
        estimated token budget (len(text) // 4) would be exceeded.
        """
        if not self.nodes:
            return ""

        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: n.calculate_weight(),
            reverse=True,
        )

        # Build an index of outgoing edges per source node
        outgoing: Dict[str, List[MemoryEdge]] = {}
        for edge in self.edges:
            outgoing.setdefault(edge.source_id, []).append(edge)

        lines: List[str] = ["## Relevant Memory Context"]
        tokens_used = len(lines[0]) // 4

        for node in sorted_nodes:
            node_line = f"- [{node.node_type}] {node.content}"
            rel_lines: List[str] = []
            for edge in outgoing.get(node.id, []):
                target = self.nodes.get(edge.target_id)
                if target:
                    rel_lines.append(f"  \u2192 {edge.edge_type}: {target.content}")

            section_text = node_line + ("\n" + "\n".join(rel_lines) if rel_lines else "")
            section_tokens = len(section_text) // 4

            if max_tokens is not None and tokens_used + section_tokens > max_tokens:
                break

            lines.append(section_text)
            tokens_used += section_tokens

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    def build_context_for_query(self, query: str, token_budget: int = 500) -> str:
        """Main entry point for query-time context retrieval.

        Scores each node against the query using keyword matching combined with
        the node's calculate_weight(). Picks up to 3 seed nodes, builds local
        slices around them, merges slices, and returns a prompt-ready string.

        Scoring: 0.5 * (keyword_match_ratio) + 0.5 * node.calculate_weight()
        Accessed nodes get their access_count incremented and last_accessed updated.
        Emits a MemoryRetrievalLog stored in self.last_retrieval_log.
        """
        start_time = time.time()

        if not self.nodes:
            self.last_retrieval_log = MemoryRetrievalLog(
                query=query, nodes_scored=0, nodes_returned=0, nodes_dropped=0,
                dropped_node_ids=[], top_scores=[], token_budget=token_budget,
                tokens_used=0, elapsed_ms=(time.time() - start_time) * 1000,
            )
            self.retrieval_history.append(self.last_retrieval_log)
            self.metrics.record_retrieval(self.last_retrieval_log)
            logger.info(f"Memory retrieval: {self.last_retrieval_log}")
            return ""

        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if w not in _STOPWORDS]

        # Score each node
        scored: List[Tuple[MemoryNode, float]] = []
        for node in self.nodes.values():
            content_lower = node.content.lower()
            if query_words:
                matches = sum(1 for w in query_words if w in content_lower)
                query_score = matches / len(query_words)
            else:
                query_score = 0.0
            combined = 0.5 * query_score + 0.5 * node.calculate_weight()
            scored.append((node, combined))

        scored.sort(key=lambda item: item[1], reverse=True)
        nodes_scored = len(scored)

        # Pick seed nodes: top 3 with combined > 0, or fallback to top 3 by weight
        seeds = [node for node, score in scored[:3] if score > 0]
        if not seeds:
            seeds = [node for node, _ in scored[:3]]

        # Update access tracking on seed nodes
        now = datetime.utcnow()
        for node in seeds:
            node.access_count += 1
            node.last_accessed = now

        # Build and merge slices from seed nodes
        merged = self.build_local_slice(seeds[0].id, token_budget)
        for seed in seeds[1:]:
            if seed.id in merged.nodes:
                continue
            extra_slice = self.build_local_slice(seed.id, token_budget)
            for node in extra_slice.nodes.values():
                if node.id not in merged.nodes:
                    merged.add_node(node)
            for edge in extra_slice.edges:
                if edge.source_id in merged.nodes and edge.target_id in merged.nodes:
                    if edge not in merged.edges:
                        merged.edges.append(edge)

        result = merged.to_prompt_context(max_tokens=token_budget)

        # Build retrieval log
        returned_ids: Set[str] = set(merged.nodes.keys())
        all_scored_ids = {node.id for node, _ in scored}
        dropped_ids = sorted(all_scored_ids - returned_ids)
        top_scores = [(node.id, score) for node, score in scored if node.id in returned_ids]

        self.last_retrieval_log = MemoryRetrievalLog(
            query=query,
            nodes_scored=nodes_scored,
            nodes_returned=len(returned_ids),
            nodes_dropped=len(dropped_ids),
            dropped_node_ids=dropped_ids,
            top_scores=top_scores,
            token_budget=token_budget,
            tokens_used=len(result) // 4,
            elapsed_ms=(time.time() - start_time) * 1000,
        )
        self.retrieval_history.append(self.last_retrieval_log)
        self.metrics.record_retrieval(self.last_retrieval_log)
        logger.info(f"Memory retrieval: {self.last_retrieval_log}")

        return result

    def find_related(self, node_id: str, max_results: Optional[int] = None) -> List[Tuple[MemoryNode, float]]:
        """Find nodes connected to node_id via any edge direction, sorted by weight descending.

        Returns a list of (MemoryNode, weight) tuples. If max_results is given,
        returns at most that many results.
        """
        related: List[Tuple[MemoryNode, float]] = []
        for edge in self.edges:
            if edge.source_id == node_id:
                related.append((self.nodes[edge.target_id], edge.weight))
            elif edge.target_id == node_id:
                related.append((self.nodes[edge.source_id], edge.weight))
        related.sort(key=lambda item: item[1], reverse=True)
        if max_results is not None:
            return related[:max_results]
        return related
