"""
Main Orchestrator - Integrates all components for intelligent query processing

This is the "brain" that coordinates:
1. QueryAnalyzer - understands the question
2. MemoryEvaluator - checks what we know
3. DecisionEngine - decides how to respond
4. Response Generation - creates the answer
5. Memory Update - saves new facts
"""

from typing import Optional, Dict, Any, List
import time
import logging

# These will import the components we already built
from app.services.orchestrator.query_analyzer import QueryAnalyzer, QueryAnalysis
from app.services.orchestrator.memory_evaluator import MemoryEvaluator, MemoryEvaluation
from app.services.orchestrator.decision_engine import DecisionEngine, ResponseStrategy
from app.services.orchestrator.response_formatter import ResponseFormatter
from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics
from app.services.orchestrator.reasoning_planner import ReasoningPlanner
from app.services.orchestrator.synthesis_engine import SynthesisEngine
from app.services.orchestrator.response_cache import ResponseCache
from app.services.orchestrator.chain_builder import ChainBuilder
from app.services.orchestrator.chain_executor import ChainExecutor
from app.services.orchestrator.ab_testing import ABTestingService

logger = logging.getLogger(__name__)


class IntelligentOrchestrator:
    """
    Main orchestrator that coordinates all components.

    Think of this as a conductor of an orchestra:
    - Each component (QueryAnalyzer, MemoryEvaluator, etc.) is an instrument
    - The orchestrator coordinates them to create beautiful music (responses)
    """

    def __init__(
            self,
            memory_service,  # Handles memory storage/retrieval
            agent_registry,  # Manages AI agents (Mistral, DeepSeek, etc.)
            fact_extractor=None,  # Extracts facts from conversations
            web_search_service=None,  # Web search for external info
            response_cache=None,  # Cache for responses
            ab_testing_service=None  # A/B testing service
    ):
        """
        Initialize the orchestrator with required services.
        Args:
            memory_service: Service for storing/retrieving facts
            agent_registry: Registry of available AI agents
            fact_extractor: Service for extracting facts (optional)
            web_search_service: Web search for external info (optional)
            response_cache: Cache for responses (optional, created if not provided)
        """
        # Store the services we need
        self.memory_service = memory_service
        self.agent_registry = agent_registry
        self.fact_extractor = fact_extractor
        self.web_search_service = web_search_service
        self.response_cache = response_cache or ResponseCache()
        self.ab_testing_service = ab_testing_service

        # Create instances of our components
        self.query_analyzer = QueryAnalyzer()
        self.memory_evaluator = MemoryEvaluator(memory_service)
        self.decision_engine = DecisionEngine()
        self.response_formatter = ResponseFormatter()
        self.metrics = OrchestratorMetrics()
        self.reasoning_planner = ReasoningPlanner()
        self.synthesis_engine = SynthesisEngine()
        self.chain_builder = ChainBuilder()
        self.chain_executor = ChainExecutor()

        logger.info("IntelligentOrchestrator initialized successfully")

    async def process_query(
            self,
            query: str,
            session_id: str,
            user_context: Optional[Dict[str, Any]] = None,
            use_chains: bool = False,
            user_id: Optional[str] = None,
            ab_experiment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method - processes a user query through all stages.

        This is like a pipeline:
        Query → Analyze → Check Memory → Decide → Generate → Update Memory → Response

        Args:
            query: The user's question/input
            session_id: Current conversation session
            user_context: Optional additional context

        Returns:
            Dictionary with response and metadata:
            {
                "text": "The actual response",
                "metadata": {
                    "strategy": "direct/enhanced/deep_reasoning",
                    "confidence": 0.95,
                    "sources": ["memory", "mistral"],
                    "elapsed_time_ms": 150.5,
                    "cost_usd": 0.0001
                }
            }
        """
        start_time = time.time()

        try:
            logger.info(f"Processing query for session {session_id}: {query[:50]}...")

            # ==========================================
            # A/B TESTING: Get variant if experiment active
            # ==========================================
            ab_variant = None
            if self.ab_testing_service and ab_experiment_id and user_id:
                ab_variant = self.ab_testing_service.get_variant(ab_experiment_id, user_id)
                logger.info(f"A/B Testing: Using variant '{ab_variant}' for experiment {ab_experiment_id}")

            # ==========================================
            # CHECK CACHE FIRST
            # ==========================================
            cached_response = self.response_cache.get(query, context=user_context)
            if cached_response is not None:
                logger.info("Cache hit - returning cached response")
                elapsed_time = (time.time() - start_time) * 1000
                cached_response["metadata"]["elapsed_time_ms"] = round(elapsed_time, 2)
                cached_response["metadata"]["cached"] = True
                return cached_response

            # ==========================================
            # STAGE 1: Analyze the Query
            # ==========================================
            # Understand: Is it simple? Complex? What's it about?
            logger.debug("Stage 1: Analyzing query")
            query_analysis = self.query_analyzer.analyze(
                query=query
            )
            logger.debug(f"Query complexity: {query_analysis.complexity}")

            # ==========================================
            # STAGE 2: Check Memory Coverage
            # ==========================================
            # Do we already know the answer from past conversations?
            logger.debug("Stage 2: Evaluating memory coverage")
            memory_eval = await self.memory_evaluator.evaluate(
                query_analysis=query_analysis,
                session_id=session_id
            )
            logger.debug(f"Memory coverage: {memory_eval.coverage_score:.2f}")

            # ==========================================
            # STAGE 3: Decide Response Strategy
            # ==========================================
            # Should we answer directly, use AI, or do deep reasoning?
            logger.debug("Stage 3: Deciding response strategy")
            strategy = self.decision_engine.decide(
                query_analysis=query_analysis,
                memory_eval=memory_eval
            )

            # A/B Testing: Override strategy if variant is active
            if ab_variant and ab_variant in ["direct", "enhanced", "deep_reasoning"]:
                original_strategy = strategy.strategy
                strategy.strategy = ab_variant
                logger.info(f"A/B Testing: Overriding strategy '{original_strategy}' -> '{ab_variant}'")

            logger.info(f"Selected strategy: {strategy.strategy}")

            # ==========================================
            # STAGE 4: Generate Response (Chain Mode)
            # ==========================================
            if use_chains:
                logger.debug("Stage 4: Executing chain")
                chain = self.chain_builder.build(query, memory_eval.coverage_score)
                chain_result = await self._execute_chain(chain, memory_eval)

                elapsed_time = (time.time() - start_time) * 1000

                result = {
                    "text": chain_result["text"],
                    "metadata": {
                        "strategy": strategy.strategy,
                        "confidence": query_analysis.confidence,
                        "sources": chain_result["sources"],
                        "elapsed_time_ms": round(elapsed_time, 2),
                        "cost_usd": strategy.estimated_cost,
                        "reasoning_depth": strategy.reasoning_depth,
                        "memory_coverage": round(memory_eval.coverage_score, 2),
                        "chain_executed": True,
                        "chain_steps": len(chain.steps)
                    }
                }

                # Update memory
                await self._extract_and_save_facts(
                    session_id=session_id,
                    query=query,
                    response=chain_result["text"]
                )

                # Track metrics
                self.metrics.track_query(
                    strategy=strategy.strategy,
                    elapsed_time_ms=elapsed_time,
                    cost_usd=strategy.estimated_cost
                )

                # Cache direct chain answers for reuse (1 step = direct)
                if len(chain.steps) == 1:
                    self.response_cache.set(query, result, context=user_context)
                    logger.debug("Cached chain direct response")

                return result

            # ==========================================
            # STAGE 4: Generate Response
            # ==========================================
            # Actually create the response based on the strategy
            logger.debug("Stage 4: Generating response")
            reasoning_steps = []  # Only populated for deep_reasoning
            synthesis_confidence = None  # Only populated for deep_reasoning

            if strategy.strategy == "direct":
                # Answer directly from memory (fast, free)
                response_text = self._direct_answer(memory_eval.relevant_facts)
                sources = ["memory"]

            elif strategy.strategy == "enhanced":
                # Use AI with memory context (balanced)
                response_text, sources = await self._enhanced_answer(
                    query=query,
                    memory_facts=memory_eval.relevant_facts,
                    strategy=strategy
                )

            else:  # deep_reasoning
                # Deep thinking with AI (slow, thorough)
                response_text, sources, reasoning_steps, synthesis_confidence = await self._deep_reasoning_answer(
                    query=query,
                    query_analysis=query_analysis,
                    memory_eval=memory_eval,
                    strategy=strategy
                )

            # ==========================================
            # STAGE 5: Update Memory
            # ==========================================
            # Save new facts from this conversation
            logger.debug("Stage 5: Updating memory")
            await self._extract_and_save_facts(
                session_id=session_id,
                query=query,
                response=response_text
            )

            # ==========================================
            # Calculate Metrics and Return
            # ==========================================
            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            result = {
                "text": response_text,
                "metadata": {
                    "strategy": strategy.strategy,
                    "confidence": query_analysis.confidence,
                    "sources": sources,
                    "elapsed_time_ms": round(elapsed_time, 2),
                    "cost_usd": strategy.estimated_cost,
                    "reasoning_depth": strategy.reasoning_depth,
                    "memory_coverage": round(memory_eval.coverage_score, 2),
                    "reasoning_steps": reasoning_steps,
                    "synthesis_confidence": synthesis_confidence if strategy.strategy == "deep_reasoning" else None,
                    "ab_variant": ab_variant
                }
            }

            logger.info(f"Query processed in {elapsed_time:.2f}ms using {strategy.strategy} strategy")

            # Track metrics
            self.metrics.track_query(
                strategy=strategy.strategy,
                elapsed_time_ms=elapsed_time,
                cost_usd=strategy.estimated_cost
            )

            # Cache direct answers for reuse
            if strategy.strategy == "direct":
                self.response_cache.set(query, result, context=user_context)
                logger.debug("Cached direct response")

            # ==========================================
            # A/B TESTING: Record result
            # ==========================================
            if self.ab_testing_service and ab_experiment_id and user_id and ab_variant:
                self.ab_testing_service.record_result(
                    experiment_id=ab_experiment_id,
                    variant=ab_variant,
                    user_id=user_id,
                    success=True,  # Query completed successfully
                    latency_ms=elapsed_time
                )
                logger.debug(f"A/B Testing: Recorded result for variant '{ab_variant}'")

            return result

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            # Return a safe error response
            return {
                "text": "I apologize, but I encountered an error processing your request. Please try again.",
                "metadata": {
                    "strategy": "error",
                    "confidence": 0.0,
                    "sources": [],
                    "elapsed_time_ms": (time.time() - start_time) * 1000,
                    "cost_usd": 0.0,
                    "error": str(e)
                }
            }

    def _direct_answer(self, facts: List[Dict[str, Any]]) -> str:
        """
        Generate a direct answer from memory facts.
        This is FAST (no AI needed) and FREE.

        Uses ResponseFormatter to format the response properly.
        """
        if not facts:
            return "I don't have that information in my memory yet."

        # Use ResponseFormatter to format facts nicely
        return self.response_formatter.format_direct(facts)

    async def _enhanced_answer(
            self,
            query: str,
            memory_facts: List[Dict[str, Any]],
            strategy: ResponseStrategy
    ) -> tuple[str, List[str]]:
        """
        Generate an enhanced answer using AI + memory.
        This is BALANCED - uses AI but with memory context to be more relevant.
        Uses ResponseFormatter to format the response with context.
        """
        # Build context from memory (sorted by importance)
        context = self._build_context(memory_facts, max_facts=5)

        # Create enhanced prompt
        enhanced_prompt = f"""Context from previous conversations:
    {context}

    User question: {query}

    Please provide a helpful response using the context above."""

        # Select agent based on strategy preference
        agent = self._select_agent(strategy.agent_preference)

        if agent:
            # Call the AI agent
            ai_response = await agent.process(enhanced_prompt)

            # Format with ResponseFormatter
            formatted_response = self.response_formatter.format_enhanced(
                ai_response=ai_response,
                context_facts=memory_facts[:3]  # Top 3 facts for context
            )

            return formatted_response, ["memory", agent.name]
        else:
            # Fallback if no agent available
            return self._direct_answer(memory_facts), ["memory"]

    async def _deep_reasoning_answer(
            self,
            query: str,
            query_analysis: QueryAnalysis,
            memory_eval: MemoryEvaluation,
            strategy: ResponseStrategy
    ) -> tuple[str, List[str], List[str], float]:
        """
        Generate a deep, thoughtful answer for complex queries.
        This is SLOW but THOROUGH - uses premium AI with multiple reasoning steps.
        Uses ResponseFormatter to preserve paragraph structure.
        """
        # Create reasoning plan
        plan = self.reasoning_planner.create_plan(
            query=query,
            query_analysis=query_analysis,
            memory_eval=memory_eval
        )
        reasoning_steps = [f"{s.step_number}. {s.action}: {s.description}" for s in plan.steps]

        # Execute web search if in plan and service available
        web_search_results = []
        if self.web_search_service:
            for step in plan.steps:
                if step.action == "web_search" and memory_eval.gaps:
                    search_query = " ".join(memory_eval.gaps[:2])  # Top 2 gaps
                    web_search_results = await self.web_search_service.search(
                        query=search_query,
                        max_results=3
                    )
                    break  # Only one web search per query

        # Build comprehensive context
        context_parts = []
        # Add memory context (sorted by importance)
        # Build comprehensive context
        context_parts = []
        # Add memory context (sorted by importance)
        if memory_eval.relevant_facts:
            facts_text = self._build_context(memory_eval.relevant_facts, max_facts=10)
            context_parts.append(f"Known information:\n{facts_text}")

        # Add information gaps
        if memory_eval.gaps:
            gaps_text = ", ".join(memory_eval.gaps)
            context_parts.append(f"Information gaps: {gaps_text}")

        # Add web search results
        if web_search_results:
            web_text = "\n".join([
                f"- {r.get('title', '')}: {r.get('snippet', '')}"
                for r in web_search_results if not r.get('error')
            ])
            if web_text:
                context_parts.append(f"Web search results:\n{web_text}")

        context = "\n\n".join(context_parts)

        # Create deep reasoning prompt
        deep_prompt = f"""You are analyzing a complex question that requires deep thinking.
    Question: {query}
    {context}
    Please provide a comprehensive, well-reasoned response. Think through this step by step."""
        # Use premium agent (e.g., Mixtral, DeepSeek)
        agent = self._select_agent("premium")
        if agent:
            ai_response = await agent.process(deep_prompt)

            # Synthesize from all sources
            synthesis_result = self.synthesis_engine.synthesize(
                memory_facts=memory_eval.relevant_facts,
                web_results=web_search_results,
                ai_analysis=ai_response
            )

            # Format with ResponseFormatter (preserves paragraphs)
            formatted_response = self.response_formatter.format_deep(ai_response)
            return formatted_response, ["memory", agent.name, "deep_reasoning"], reasoning_steps, synthesis_result.confidence
        else:
            # Fallback
            return "I apologize, but I need a more powerful AI model to answer this complex question properly.", [
                "error"], reasoning_steps, 0.3

    def _select_agent(self, preference: str) -> Optional[Any]:
        """
        Select an AI agent based on preference.

        Args:
            preference: "fast", "balanced", or "premium"

        Returns:
            Selected agent or None
        """
        # Agent preference mapping
        agent_map = {
            "fast": ["groq", "llama3"],  # Fast models
            "balanced": ["mistral", "deepseek"],  # Balanced models
            "premium": ["mixtral", "deepseek"]  # Premium models
        }

        preferred_agents = agent_map.get(preference, ["mistral"])

        # Try to get first available agent
        for agent_name in preferred_agents:
            agent = self.agent_registry.get_agent(agent_name)
            if agent:
                return agent

        # Fallback to any available agent
        return self.agent_registry.get_default_agent()

    def _build_context(self, facts: List[Dict[str, Any]], max_facts: int = 5) -> str:
        """
        Build context string from memory facts, sorted by importance.

        Args:
            facts: List of fact dictionaries with 'text', 'importance', 'confidence'
            max_facts: Maximum number of facts to include

        Returns:
            Formatted context string with facts sorted by importance
        """
        if not facts:
            return ""

        # Sort by importance (highest first)
        sorted_facts = sorted(
            facts,
            key=lambda f: f.get('importance', 0.5),
            reverse=True
        )

        # Take top N facts
        top_facts = sorted_facts[:max_facts]

        # Format as context string
        context_lines = [f"- {fact.get('text', '')}" for fact in top_facts]
        return "\n".join(context_lines)

    async def _extract_and_save_facts(
            self,
            session_id: str,
            query: str,
            response: str
    ) -> None:
        """
        Extract and save facts from this conversation turn.
        This keeps our memory up-to-date.

        Args:
            session_id: Current session
            query: User's query
            response: Our response
        """
        if not self.fact_extractor:
            logger.debug("No fact extractor configured, skipping memory update")
            return

        try:
            # Extract facts from the conversation
            conversation_text = f"User: {query}\nAssistant: {response}"
            facts = await self.fact_extractor.extract_facts(
                conversation_text=conversation_text,
                session_id=session_id
            )

            # Save facts to memory
            if facts:
                logger.info(f"Extracted {len(facts)} new facts")
                for fact in facts:
                    await self.memory_service.add_fact(fact, session_id)

        except Exception as e:
            # Don't fail the whole request if memory update fails
            logger.warning(f"Failed to update memory: {str(e)}")

    async def _execute_chain(self, chain, memory_eval) -> dict:
        """
        Execute a chain of steps using ChainExecutor.

        Args:
            chain: ExecutionChain from ChainBuilder
            memory_eval: Memory evaluation results

        Returns:
            Dictionary with response text and sources
        """
        sources = []
        context_from_memory = ""
        web_results = []

        async def step_handler(step, previous_results):
            """Handle each step type."""
            nonlocal context_from_memory, web_results

            if step.step_type == "direct":
                sources.append("memory")
                return self._direct_answer(memory_eval.relevant_facts)
            elif step.step_type == "memory":
                sources.append("memory")
                context_from_memory = self._build_context(memory_eval.relevant_facts, max_facts=5)
                return context_from_memory
            elif step.step_type == "web_search":
                sources.append("web")
                if self.web_search_service:
                    web_results = await self.web_search_service.search(step.prompt)
                    return web_results
                return []
            elif step.step_type == "analysis":
                sources.append(step.agent)
                agent = self.agent_registry.get_agent(step.agent)
                prompt = step.prompt
                if context_from_memory:
                    prompt = f"Context:\n{context_from_memory}\n\nQuestion: {step.prompt}"
                response = await agent.process(prompt)
                return response
            elif step.step_type == "synthesis":
                sources.append(step.agent)
                agent = self.agent_registry.get_agent(step.agent)
                # Build context from previous results
                prev_outputs = [r.output for r in previous_results if r.success]
                synthesis_context = "\n".join(str(o) for o in prev_outputs)
                prompt = f"Previous analysis:\n{synthesis_context}\n\nSynthesize a final answer for: {step.prompt}"
                response = await agent.process(prompt)
                return response
            else:
                # Default: return step type as placeholder
                sources.append(step.agent)
                return f"Executed {step.step_type}"

        # Execute chain with custom handler
        from app.services.orchestrator.chain_executor import ChainExecutor
        executor = ChainExecutor(step_handler=step_handler)
        result = await executor.execute(chain)

        return {
            "text": result.final_output or "No response generated",
            "sources": sources
        }
# ==========================================
# Convenience Functions
# ==========================================

def create_orchestrator(
        memory_service,
        agent_registry,
        fact_extractor=None
) -> IntelligentOrchestrator:
    """
    Factory function to create an orchestrator.
    Makes it easier to create one with proper setup.

    Args:
        memory_service: Memory service instance
        agent_registry: Agent registry instance
        fact_extractor: Fact extractor instance (optional)

    Returns:
        Configured IntelligentOrchestrator instance
    """
    return IntelligentOrchestrator(
        memory_service=memory_service,
        agent_registry=agent_registry,
        fact_extractor=fact_extractor
    )