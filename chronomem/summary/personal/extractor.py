# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/summary/personal/extractor.py
# Purpose: Extract personal memories from conversations (ReMe adaptation)
# ===========================================================================

"""
Personal Memory Extractor

Adapted from ReMe's get_observation_op.py with full capabilities:
- Basic observation extraction
- Time-aware observation extraction
- Duplicate/contradiction checking
- Information filtering
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple

from chronomem.schema.memory import PersonalMemory
from chronomem.core.datetime_handler import DatetimeHandler
from chronomem.core.embedder import get_embedder


# =============================================================================
# Prompts (adapted from ReMe)
# =============================================================================

OBSERVATION_SYSTEM_PROMPT = """You are an assistant that extracts personal information about {user_name} from conversations.

Your task:
1. Read the conversation messages
2. Extract factual, reusable personal information
3. Output in the specified format

Rules:
- Only extract FACTS about the user (preferences, habits, constraints)
- Skip greetings, questions, vague statements
- Focus on learning-related information
- Output "None" if no meaningful information found

Output format for each observation:
Information: <index> <> <content> <keywords>

Where:
- <index>: Message number the info came from
- <content>: Clear, concise description of the personal info
- <keywords>: Keywords for retrieval (comma-separated)"""

OBSERVATION_WITH_TIME_PROMPT = """You are an assistant that extracts TIME-RELATED personal information about {user_name}.

Focus on extracting information about:
- When the user prefers to study
- Regular schedules and routines
- Time-based preferences and constraints

Output format:
Information: <index> <time_info> <content> <keywords>

Where:
- <index>: Message number
- <time_info>: The time-related detail (e.g., "every morning", "weekends")
- <content>: The personal information
- <keywords>: Keywords for retrieval"""

CONTRA_REPEAT_PROMPT = """Compare the new memory with existing memories.

New memory: {new_content}

Existing memories:
{existing_memories}

Determine if the new memory is:
1. DUPLICATE - Same information as an existing memory
2. CONTRADICT - Conflicts with an existing memory (return which one)
3. NEW - Unique, non-conflicting information

Output exactly one of:
- DUPLICATE
- CONTRADICT:<memory_id>
- NEW"""

INFO_FILTER_PROMPT = """Evaluate if this information is worth storing as a personal memory:

Information: {content}

Criteria:
- Is it factual and specific? (not vague)
- Is it reusable in future conversations?
- Is it about the user's preferences, habits, or constraints?
- Is it relevant to learning and studying?

Output: KEEP or DISCARD"""


class PersonalExtractor:
    """
    Extract personal memories from conversations.
    
    Implements ReMe's full extraction pipeline:
    1. Basic observation extraction
    2. Time-aware extraction
    3. Duplicate checking
    4. Information filtering
    """
    
    def __init__(self, language: str = "en"):
        """Initialize extractor."""
        self.language = language
        self.embedder = get_embedder()
    
    async def extract(
        self,
        messages: List[Dict[str, Any]],
        user_id: str = "default",
        user_name: str = "user",
        existing_memories: Optional[List[PersonalMemory]] = None,
    ) -> List[PersonalMemory]:
        """
        Extract personal memories from conversation messages.
        
        Args:
            messages: List of {role, content} message dicts.
            user_id: User identifier.
            user_name: User's name for prompts.
            existing_memories: Existing memories for dedup checking.
        
        Returns:
            List of extracted PersonalMemory objects.
        """
        if not messages:
            return []
        
        # Separate into time-related and non-time-related messages
        time_messages = []
        regular_messages = []
        
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if DatetimeHandler.has_time_word(content, self.language):
                    time_messages.append(msg)
                else:
                    regular_messages.append(msg)
        
        all_memories = []
        
        # Extract regular observations
        if regular_messages:
            memories = await self._extract_observations(
                regular_messages, user_id, user_name
            )
            all_memories.extend(memories)
        
        # Extract time-aware observations
        if time_messages:
            memories = await self._extract_with_time(
                time_messages, user_id, user_name
            )
            all_memories.extend(memories)
        
        # Filter and deduplicate
        if existing_memories:
            all_memories = await self._deduplicate(all_memories, existing_memories)
        
        all_memories = await self._filter_memories(all_memories)
        
        # Generate embeddings
        for memory in all_memories:
            embed_text = f"{memory.when_to_use} {memory.content}"
            memory.embedding = await self.embedder.embed(embed_text)
        
        return all_memories
    
    async def _extract_observations(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        user_name: str,
    ) -> List[PersonalMemory]:
        """Extract basic observations from messages."""
        from services.gemini_service import create_gemini_service
        
        service = create_gemini_service()
        if not service:
            return []
        
        # Format messages for prompt
        msg_list = []
        for i, msg in enumerate(messages):
            msg_list.append(f"{i+1} {user_name}: {msg.get('content', '')[:300]}")
        
        prompt = f"""{OBSERVATION_SYSTEM_PROMPT.format(user_name=user_name)}

Conversation messages:
{chr(10).join(msg_list)}

Extract personal information (up to {len(messages)} observations):"""
        
        try:
            response = await service.send_message(prompt)
            return self._parse_observations(response, messages, user_id)
        except Exception as e:
            print(f"Observation extraction failed: {e}")
            return []
    
    async def _extract_with_time(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        user_name: str,
    ) -> List[PersonalMemory]:
        """Extract time-aware observations."""
        from services.gemini_service import create_gemini_service
        
        service = create_gemini_service()
        if not service:
            return []
        
        # Format messages with timestamps
        msg_list = []
        for i, msg in enumerate(messages):
            content = msg.get("content", "")[:300]
            time_info = DatetimeHandler.extract_time_info(content, self.language)
            msg_list.append(f"{i+1} [Time hint: {time_info or 'N/A'}] {user_name}: {content}")
        
        prompt = f"""{OBSERVATION_WITH_TIME_PROMPT.format(user_name=user_name)}

Conversation messages:
{chr(10).join(msg_list)}

Extract time-related personal information:"""
        
        try:
            response = await service.send_message(prompt)
            return self._parse_time_observations(response, messages, user_id)
        except Exception as e:
            print(f"Time observation extraction failed: {e}")
            return []
    
    async def _deduplicate(
        self,
        new_memories: List[PersonalMemory],
        existing: List[PersonalMemory],
    ) -> List[PersonalMemory]:
        """Remove duplicates and handle contradictions."""
        if not existing:
            return new_memories
        
        from services.gemini_service import create_gemini_service
        
        service = create_gemini_service()
        if not service:
            return new_memories
        
        result = []
        existing_text = "\n".join([
            f"- [{m.id[:8]}] {m.content}" for m in existing[:10]
        ])
        
        for memory in new_memories:
            prompt = CONTRA_REPEAT_PROMPT.format(
                new_content=memory.content,
                existing_memories=existing_text,
            )
            
            try:
                response = await service.send_message(prompt)
                response = response.strip().upper()
                
                if "DUPLICATE" in response:
                    continue  # Skip duplicate
                elif "CONTRADICT" in response:
                    # Could update the conflicting memory, for now just add
                    memory.metadata["contradicts"] = response
                    result.append(memory)
                else:
                    result.append(memory)
            except Exception:
                result.append(memory)
        
        return result
    
    async def _filter_memories(
        self,
        memories: List[PersonalMemory],
    ) -> List[PersonalMemory]:
        """Filter out low-value memories."""
        from services.gemini_service import create_gemini_service
        
        service = create_gemini_service()
        if not service:
            return memories
        
        result = []
        
        for memory in memories:
            prompt = INFO_FILTER_PROMPT.format(content=memory.content)
            
            try:
                response = await service.send_message(prompt)
                if "KEEP" in response.upper():
                    result.append(memory)
            except Exception:
                result.append(memory)
        
        return result
    
    def _parse_observations(
        self,
        response: str,
        messages: List[Dict[str, Any]],
        user_id: str,
    ) -> List[PersonalMemory]:
        """Parse LLM response into PersonalMemory objects."""
        # Pattern: Information: <1> <> <content> <keywords>
        pattern = r"Information:\s*<(\d+)>\s*<>\s*<([^<>]+)>\s*<([^<>]*)>"
        matches = re.findall(pattern, response, re.IGNORECASE)
        
        memories = []
        for match in matches:
            idx_str, content, keywords = match
            content = content.strip()
            
            if content.lower() in ["none", "无", "", "repeat"]:
                continue
            
            try:
                idx = int(idx_str) - 1
                source = messages[idx].get("content", "") if idx < len(messages) else ""
            except (ValueError, IndexError):
                source = ""
            
            memory = PersonalMemory.from_observation(
                content=content,
                keywords=keywords.strip(),
                user_id=user_id,
                source_message=source,
            )
            memories.append(memory)
        
        return memories
    
    def _parse_time_observations(
        self,
        response: str,
        messages: List[Dict[str, Any]],
        user_id: str,
    ) -> List[PersonalMemory]:
        """Parse time-aware observations."""
        # Pattern: Information: <1> <time_info> <content> <keywords>
        pattern = r"Information:\s*<(\d+)>\s*<([^<>]*)>\s*<([^<>]+)>\s*<([^<>]*)>"
        matches = re.findall(pattern, response, re.IGNORECASE)
        
        memories = []
        for match in matches:
            idx_str, time_info, content, keywords = match
            content = content.strip()
            
            if content.lower() in ["none", "无", "", "repeat"]:
                continue
            
            try:
                idx = int(idx_str) - 1
                source = messages[idx].get("content", "") if idx < len(messages) else ""
            except (ValueError, IndexError):
                source = ""
            
            memory = PersonalMemory.from_observation(
                content=content,
                keywords=keywords.strip(),
                user_id=user_id,
                time_info=time_info.strip() if time_info else None,
                source_message=source,
            )
            memories.append(memory)
        
        return memories
