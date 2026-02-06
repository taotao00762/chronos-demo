# ===========================================================================
# Chronos AI Learning Companion
# File: memory/reme_client.py
# Purpose: ReMe AI memory service client
# ===========================================================================

"""
ReMe Client

Wrapper for ReMe AI memory service using embedded ReMeApp.
Provides personal, task, and working memory operations.

Usage:
    async with ReMeClient() as client:
        await client.summary_personal_memory(...)
        result = await client.retrieve_personal_memory(...)
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add ReMe to path
REME_PATH = Path("E:/baoke/ReMe-main")
if str(REME_PATH) not in sys.path:
    sys.path.insert(0, str(REME_PATH))

from memory.workspace import get_personal_workspace, get_task_workspace


class ReMeClient:
    """
    Async client for ReMe memory operations.
    
    Uses embedded ReMeApp for local operation (no HTTP server needed).
    """
    
    def __init__(
        self,
        llm_model: str = "gemini-3-flash-preview",
        embedding_model: str = "text-embedding-004",
        vector_backend: str = "memory",
    ):
        """
        Initialize ReMe client configuration.
        
        Args:
            llm_model: LLM model for summarization.
            embedding_model: Embedding model for vector search.
            vector_backend: Vector store backend (memory/local/chromadb).
        """
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.vector_backend = vector_backend
        self._app = None
    
    async def __aenter__(self):
        """Enter async context - initialize ReMeApp."""
        from reme_ai import ReMeApp
        self._app = ReMeApp(
            f"llm.default.model_name={self.llm_model}",
            f"embedding_model.default.model_name={self.embedding_model}",
            f"vector_store.default.backend={self.vector_backend}",
        )
        await self._app.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - cleanup ReMeApp."""
        if self._app:
            await self._app.__aexit__(exc_type, exc_val, exc_tb)
            self._app = None
    
    # =========================================================================
    # Personal Memory
    # =========================================================================
    
    async def summary_personal_memory(
        self,
        trajectories: List[Dict[str, Any]],
        user_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Extract and store personal memories from trajectories.
        
        Args:
            trajectories: List of conversation trajectories.
            user_id: User identifier.
        
        Returns:
            ReMe operation result.
        """
        workspace_id = get_personal_workspace(user_id)
        return await self._app.async_execute(
            name="summary_personal_memory",
            workspace_id=workspace_id,
            trajectories=trajectories,
        )
    
    async def retrieve_personal_memory(
        self,
        query: str,
        user_id: str = "default",
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant personal memories.
        
        Args:
            query: Search query.
            user_id: User identifier.
            top_k: Number of results to return.
        
        Returns:
            List of memory items.
        """
        workspace_id = get_personal_workspace(user_id)
        result = await self._app.async_execute(
            name="retrieve_personal_memory",
            workspace_id=workspace_id,
            query=query,
            top_k=top_k,
        )
        return result.get("memories", [])
    
    # =========================================================================
    # Task Memory
    # =========================================================================
    
    async def summary_task_memory(
        self,
        trajectories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract and store task memories (reusable strategies).
        
        Args:
            trajectories: List of task execution trajectories with scores.
        
        Returns:
            ReMe operation result.
        """
        workspace_id = get_task_workspace()
        return await self._app.async_execute(
            name="summary_task_memory",
            workspace_id=workspace_id,
            trajectories=trajectories,
        )
    
    async def retrieve_task_memory(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant task memories (strategies).
        
        Args:
            query: Search query describing the task.
            top_k: Number of results to return.
        
        Returns:
            List of strategy items.
        """
        workspace_id = get_task_workspace()
        result = await self._app.async_execute(
            name="retrieve_task_memory",
            workspace_id=workspace_id,
            query=query,
            top_k=top_k,
        )
        return result.get("memories", [])
    
    # =========================================================================
    # Working Memory
    # =========================================================================
    
    async def summary_working_memory(
        self,
        messages: List[Dict[str, Any]],
        chat_id: str,
        max_total_tokens: int = 20000,
        keep_recent_count: int = 2,
    ) -> Dict[str, Any]:
        """
        Compact and offload long conversation context.
        
        Args:
            messages: Conversation messages.
            chat_id: Session/chat identifier.
            max_total_tokens: Token limit before compaction.
            keep_recent_count: Recent messages to keep uncompacted.
        
        Returns:
            Compacted messages and metadata.
        """
        return await self._app.async_execute(
            name="summary_working_memory",
            messages=messages,
            chat_id=chat_id,
            working_summary_mode="auto",
            max_total_tokens=max_total_tokens,
            keep_recent_count=keep_recent_count,
            store_dir="data/working_memory",
        )


# =============================================================================
# Factory Function
# =============================================================================

async def create_reme_client() -> Optional[ReMeClient]:
    """
    Factory to create and initialize ReMeClient.
    
    Returns:
        Initialized ReMeClient or None if ReMe not available.
    """
    try:
        client = ReMeClient()
        await client.__aenter__()
        return client
    except ImportError as e:
        print(f"Warning: ReMe not available: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to initialize ReMe: {e}")
        return None
