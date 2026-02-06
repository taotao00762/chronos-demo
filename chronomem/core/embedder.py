# ===========================================================================
# Chronos AI Learning Companion
# File: chronomem/core/embedder.py
# Purpose: Text embedding using Gemini
# ===========================================================================

"""
Gemini Embedder

Provides text embedding using Google's text-embedding model.
"""

import os
from typing import List, Optional

from google import genai


class GeminiEmbedder:
    """
    Text embedder using Gemini embedding model.
    """
    
    DEFAULT_MODEL = "text-embedding-004"
    EMBEDDING_DIMENSION = 768
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
    ):
        """
        Initialize embedder.
        
        Args:
            api_key: Gemini API key (uses env var if not provided).
            model_name: Embedding model name.
        """
        self.model_name = model_name
        
        # Get API key
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            # Try to get from settings
            try:
                from services.gemini_service import get_api_key
                key = get_api_key()
            except Exception:
                pass
        
        if key:
            self.client = genai.Client(api_key=key)
        else:
            self.client = None
    
    async def embed(self, text: str) -> List[float]:
        """
        Embed a single text.
        
        Args:
            text: Text to embed.
        
        Returns:
            Embedding vector.
        """
        if not self.client:
            return [0.0] * self.EMBEDDING_DIMENSION
        
        try:
            # Truncate if too long
            text = text[:2000]
            
            result = self.client.models.embed_content(
                model=self.model_name,
                content=text,
            )
            
            return result.embeddings[0].values
        except Exception as e:
            print(f"Embedding failed: {e}")
            return [0.0] * self.EMBEDDING_DIMENSION
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts.
        
        Args:
            texts: List of texts to embed.
        
        Returns:
            List of embedding vectors.
        """
        if not self.client or not texts:
            return [[0.0] * self.EMBEDDING_DIMENSION for _ in texts]
        
        try:
            # Truncate each text
            texts = [t[:2000] for t in texts]
            
            results = []
            for text in texts:
                result = self.client.models.embed_content(
                    model=self.model_name,
                    content=text,
                )
                results.append(result.embeddings[0].values)
            
            return results
        except Exception as e:
            print(f"Batch embedding failed: {e}")
            return [[0.0] * self.EMBEDDING_DIMENSION for _ in texts]


# Singleton instance
_embedder: Optional[GeminiEmbedder] = None


def get_embedder() -> GeminiEmbedder:
    """Get or create singleton embedder."""
    global _embedder
    if _embedder is None:
        _embedder = GeminiEmbedder()
    return _embedder
