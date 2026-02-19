"""
FactExtractor Service - Automatic fact extraction from conversations

Uses gpt-oss:20b with chain-of-thought reasoning to extract structured facts
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.models.memory_v2 import Fact
from app.services.agent_service import AgentService


class FactExtractor:
    """
    Extracts facts from conversation messages using gpt-oss:20b

    Features:
    - Chain-of-thought reasoning for better extraction
    - Structured JSON output
    - Importance and confidence scoring
    - Automatic tagging
    """

    def __init__(self, agent_service: Optional[AgentService] = None):
        """
        Initialize FactExtractor

        Args:
            agent_service: Optional AgentService instance (creates new if not provided)
        """
        self.agent_service = agent_service or AgentService()
        self.model_name = "gpt-oss"  # Use gpt-oss:20b for fact extraction

    async def extract_facts(self, messages: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> List[Fact]:
        """
        Extract facts from conversation messages

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            context: Optional context information (user_id, session_id, etc.)

        Returns:
            List of extracted Fact objects

        Example:
            messages = [
                {"role": "user", "content": "I love Python programming"},
                {"role": "assistant", "content": "That's great! What do you like about it?"}
            ]
            facts = await extractor.extract_facts(messages)
        """
        # logger.info(f"Extracting facts from {len(messages)} messages")

        # Build extraction prompt
        prompt = self._build_extraction_prompt(messages, context)

        # Call gpt-oss:20b with structured output
        try:
            result = await self.agent_service.generate_response(
                prompt=prompt,
                agent_name=self.model_name,
                system_prompt=self._get_system_prompt(),
                temperature=0.3,  # Lower temperature for more deterministic output
                max_tokens=2000,
            )

            if result["status"] != "success":
                logger.error(f"Generation failed: {result.get('error')}")
                return []

            # Parse JSON response
            facts = self._parse_extraction_result(result["response"])

            logger.info(f"Extracted {len(facts)} facts")
            return facts

        except Exception as e:
            logger.error(f"Error extracting facts: {e}")
            return []

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for fact extraction

        Returns structured JSON output with facts
        """
        return """You are a fact extraction expert. Your task is to extract important, factual information ABOUT THE USER from conversations.

IMPORTANT RULES:
1. Extract only facts ABOUT THE USER (the person you are talking to)
2. Do NOT extract facts about the assistant, yourself, or AI systems
3. Each fact should be atomic (one piece of information)
4. Rate importance (0.0-1.0): how important is this fact for understanding the user?
5. Rate confidence (0.0-1.0): how confident are you this fact is accurate?
6. Add relevant tags for categorization
7. Determine fact_type: static, preference, event, weather, knowledge
8. If the message contains no facts about the user, return empty facts

OUTPUT FORMAT (JSON only, no other text):
{
  "facts": [
    {
      "text": "Clear, concise fact statement",
      "importance": 0.8,
      "confidence": 0.9,
      "fact_type": "preference",
      "tags": ["programming", "python"]
    }
  ]
}

If no important facts found, return: {"facts": []}
"""

    def _build_extraction_prompt(self, messages: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build extraction prompt from messages

        Args:
            messages: Conversation messages
            context: Optional context

        Returns:
            Formatted prompt for gpt-oss
        """
        # Format conversation
        conversation = self._format_messages(messages)

        # Build prompt with explicit examples
        prompt = f"""Extract important facts from this conversation:

    {conversation}

    CRITICAL INSTRUCTIONS:
    1. You MUST return ONLY valid JSON
    2. You MUST use this EXACT structure:
    {{"facts": [...]}}
    3. Do NOT add any text before or after the JSON
    4. Do NOT use markdown code blocks
    5. If no facts found, return: {{"facts": []}}

    REQUIRED JSON FORMAT:
    {{
      "facts": [
        {{
          "text": "User's name is John",
          "importance": 0.9,
          "confidence": 0.95,
          "fact_type": "personal",
          "tags": ["name", "identity"]
        }},
        {{
          "text": "User works as a software engineer",
          "importance": 0.8,
          "confidence": 0.9,
          "fact_type": "professional",
          "tags": ["job", "profession"]
        }}
      ]
    }}

    FACT TYPES: personal, professional, preference, knowledge, event, plan

    Now extract facts from the conversation above. Return ONLY the JSON, nothing else:"""

        return prompt
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages for prompt

        Args:
            messages: List of message dicts

        Returns:
            Formatted conversation string
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
            else:
                formatted.append(f"{role.capitalize()}: {content}")

        return "\n".join(formatted)

    def _parse_extraction_result(self, response: str) -> List[Fact]:
        """
        Parse extraction result from gpt-oss response

        Args:
            response: JSON string from model

        Returns:
            List of Fact objects
        """
        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            logger.info(f"Raw AI response (first 500 chars): {response[:500]}")  # DEBUG

            # Parse JSON
            data = json.loads(response)

            # Validate structure
            if "facts" not in data:
                logger.warning("Response missing 'facts' key")
                return []

            if not isinstance(data["facts"], list):
                logger.warning("'facts' is not a list")
                return []

            # Convert to Fact objects
            facts = []
            for fact_data in data["facts"]:
                fact = self._create_fact_from_dict(fact_data)
                if fact:
                    facts.append(fact)

            return facts

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response: {response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing extraction result: {e}")
            return []

    def _create_fact_from_dict(self, fact_data: Dict[str, Any]) -> Optional[Fact]:
        """
        Create Fact object from dictionary

        Args:
            fact_data: Dictionary with fact fields

        Returns:
            Fact object or None if invalid
        """
        try:
            # Validate required fields
            if "text" not in fact_data:
                logger.warning("Fact missing 'text' field")
                return None

            # Create Fact with defaults
            fact = Fact(
                fact_id=str(uuid.uuid4()),
                text=fact_data["text"],
                importance=self._validate_score(fact_data.get("importance", 0.5)),
                confidence=self._validate_score(fact_data.get("confidence", 0.8)),
                tags=fact_data.get("tags", []),
                fact_type=fact_data.get("fact_type", "static"),
                source="conversation",
                created=datetime.utcnow(),
                updated=datetime.utcnow(),
            )

            return fact

        except Exception as e:
            logger.error(f"Error creating fact from dict: {e}")
            return None

    def _validate_score(self, score: Any) -> float:
        """
        Validate and clamp score to 0.0-1.0 range

        Args:
            score: Score value (should be float)

        Returns:
            Validated float between 0.0 and 1.0
        """
        try:
            score = float(score)
            return max(0.0, min(1.0, score))
        except (TypeError, ValueError):
            logger.warning(f"Invalid score value: {score}, using 0.5")
            return 0.5

    async def extract_from_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Fact]:
        """
        Convenience method to extract facts from single text

        Args:
            text: Text to extract facts from
            context: Optional context

        Returns:
            List of extracted facts
        """
        messages = [{"role": "user", "content": text}]
        return await self.extract_facts(messages, context)
