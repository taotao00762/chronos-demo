# ===========================================================================
# Chronos AI Learning Companion
# File: services/image_service.py
# Purpose: Image generation service using Google Imagen API
# ===========================================================================

"""
Image Service

Generates educational images using Google Imagen API.
Used by Tutor to create visual explanations of abstract concepts.

Usage:
    service = ImageService()
    image_path = await service.generate_image("unit circle with sin/cos")
"""

import os
import uuid
import base64
from typing import Optional
from pathlib import Path

from google import genai
from google.genai import types


# =============================================================================
# Configuration
# =============================================================================

# Image model (default fallback; override with CHRONOS_IMAGE_MODEL)
DEFAULT_IMAGE_MODEL = "imagen-4.0-generate-001"
IMAGE_MODEL = DEFAULT_IMAGE_MODEL

# Image output directory
IMAGE_DIR = Path("data/images")

# Whether image generation is disabled (e.g., billing not enabled)
IMAGE_SERVICE_DISABLED = False




def _disable_image_service(reason: str) -> None:
    global IMAGE_SERVICE_DISABLED
    if IMAGE_SERVICE_DISABLED:
        return
    IMAGE_SERVICE_DISABLED = True
    print(f"ImageService: image generation disabled - {reason}")

# =============================================================================
# Image Service Class
# =============================================================================

class ImageService:
    """
    Image generation service using Google Imagen API.
    """
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the image service.
        
        Args:
            api_key: Optional API key. Uses default if not provided.
        """
        from services.gemini_service import get_api_key
        self._api_key = api_key or get_api_key()
        self._client = genai.Client(api_key=self._api_key) if self._api_key else None
        self._model_name: Optional[str] = None
        self._ignore_env_model = False
        self._used_env_model = False
        
        # Ensure image directory exists
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        name = (name or "").strip()
        if name.startswith("models/"):
            name = name[len("models/"):]
        if "/models/" in name:
            name = name.split("/models/")[-1]
        return name

    

    async def _resolve_model_name(self) -> Optional[str]:
        """Resolve the best available image model for the API key."""
        if not self._client:
            return None

        if self._model_name:
            return self._model_name

        self._used_env_model = False
        env_model_raw = os.getenv("CHRONOS_IMAGE_MODEL", "").strip()
        env_model = self._normalize_model_name(env_model_raw) if env_model_raw else ""

        try:
            candidates = []
            seen = set()
            pager = self._client.aio.models.list()
            if not hasattr(pager, "__aiter__"):
                pager = await pager
            async for model in pager:
                name = (model.name or "").strip()
                if not name:
                    continue
                actions = [a.lower() for a in (model.supported_actions or [])]
                normalized = self._normalize_model_name(name)
                if not normalized:
                    continue
                name_l = normalized.lower()
                if "imagen" in name_l:
                    if normalized not in seen:
                        candidates.append(normalized)
                        seen.add(normalized)
                elif "image" in name_l and any(a in actions for a in (
                    "predict",
                    "generatecontent",
                    "batchgeneratecontent",
                    "generateimages",
                    "generate_images",
                    "generateimage",
                    "generate_image",
                )):
                    if normalized not in seen:
                        candidates.append(normalized)
                        seen.add(normalized)

            preferred = [
                "imagen-4.0-generate-001",
                "imagen-4.0-fast-generate-001",
                "imagen-4.0-ultra-generate-001",
                "imagen-4.0-generate-preview",
                "imagen-4.0-ultra-generate-preview",
            ]
        except Exception as e:
            print(f"ImageService: model discovery failed - {e}")
            candidates = []

        if env_model and not self._ignore_env_model:
            if candidates:
                for name in candidates:
                    if env_model.lower() == name.lower():
                        self._model_name = name
                        self._used_env_model = True
                        return name
                print("ImageService: CHRONOS_IMAGE_MODEL not available; falling back to auto-detected model.")
                self._ignore_env_model = True
            else:
                self._model_name = env_model
                self._used_env_model = True
                return env_model

        for pref in preferred:
            for name in candidates:
                if pref in name.lower():
                    self._model_name = name
                    return name

        if candidates:
            self._model_name = candidates[0]
            return candidates[0]

        self._model_name = IMAGE_MODEL
        return IMAGE_MODEL

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
    ) -> Optional[str]:
        """
        Generate an educational image from text prompt.
        if IMAGE_SERVICE_DISABLED:
            return None

        
        Args:
            prompt: Description of the image to generate.
            aspect_ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4).
        
        Returns:
            Path to saved image file, or None if failed.
        """
        if not self._client:
            print("ImageService: No API key available")
            return None
        
        try:
            # Enhance prompt for educational context
            enhanced_prompt = f"Educational diagram: {prompt}. Clean, clear, professional style suitable for learning. White or light background."
            
            model_name = await self._resolve_model_name()
            if not model_name:
                print("ImageService: No image model available")
                return None

            # Generate image
            response = await self._client.aio.models.generate_images(
                model=model_name,
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    safety_filter_level="BLOCK_LOW_AND_ABOVE",
                ),
            )
            
            # Check for generated images
            if response.generated_images:
                image_data = response.generated_images[0].image.image_bytes
                
                # Save to file
                filename = f"{uuid.uuid4().hex[:12]}.png"
                filepath = IMAGE_DIR / filename
                
                with open(filepath, "wb") as f:
                    f.write(image_data)
                
                print(f"ImageService: Generated image saved to {filepath}")
                return str(filepath)
            else:
                print("ImageService: No images generated")
                return None
                
        except Exception as e:
            msg = str(e).lower()
            if "billed users" in msg or "billing" in msg:
                _disable_image_service("billing required")
                return None
            if "not found" in msg or "not supported" in msg:
                if self._used_env_model:
                    self._ignore_env_model = True
                self._model_name = None
                print("ImageService: model not found. Set CHRONOS_IMAGE_MODEL to a valid image model.")
            print(f"ImageService: Generation failed - {e}")
            return None
    
    async def close(self) -> None:
        """Close the underlying async client session if available."""
        if self._client and hasattr(self._client, "aio"):
            close = getattr(self._client.aio, "close", None)
            if callable(close):
                await close()

    def get_image_base64(self, filepath: str) -> Optional[str]:
        """
        Get base64 encoded image data for embedding.
        
        Args:
            filepath: Path to image file.
        
        Returns:
            Base64 encoded string or None.
        """
        try:
            with open(filepath, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None


# =============================================================================
# Factory Function
# =============================================================================

def create_image_service() -> Optional[ImageService]:
    """
    Factory function to create ImageService.
    
    Returns:
        ImageService instance or None if API key not available.
    """
    from services.gemini_service import get_api_key
    key = get_api_key()
    if not key:
        return None
    return ImageService(api_key=key)
