import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load env in case it's not already loaded
load_dotenv(override=True)

logger = logging.getLogger("GroqBalancer")

class GroqBalancer:
    def __init__(self):
        self._keys: List[str] = self._load_keys()
        self._index: int = 0
        
        if not self._keys:
            # Fallback to single key if the list format isn't found
            fallback_key = os.getenv("GROQ_API_KEY")
            if fallback_key:
                self._keys = [fallback_key]
                logger.info("No multiple GROQ_API_KEYS found. Using single GROQ_API_KEY from .env")
            else:
                logger.error("No Groq API keys found in environment variables!")

    def _load_keys(self) -> List[str]:
        """
        Loads keys from .env. 
        Supports format: GROQ_API_KEYS=key1,key2,key3...
        """
        raw_keys = os.getenv("GROQ_API_KEYS", "")
        if not raw_keys:
            return []
            
        # Clean and split keys
        keys = []
        for k in raw_keys.split(","):
            # Clean up: remove whitespace, backslashes (common in multiline envs), and quotes
            k = k.strip().replace("\\", "").replace("'", "").replace('"', "")
            
            if not k:
                continue
            
            # Simple validation for Groq keys (usually start with gsk_)
            # We allow non-gsk keys if they are not placeholders, but warn
            if "place" in k.lower() or "your_key" in k.lower():
                logger.warning(f"Ignoring placeholder key: {k}")
                continue
                
            if not k.startswith("gsk_"):
                logger.warning(f"Key '{k[:5]}...' does not start with 'gsk_', might be invalid.")
            
            keys.append(k)
            
        logger.info(f"Loaded {len(keys)} valid Groq API keys for load balancing.")
        return keys

    def get_next_key(self) -> Optional[str]:
        """
        Returns the next key in the round-robin sequence.
        """
        if not self._keys:
            return None
            
        key = self._keys[self._index]
        self._index = (self._index + 1) % len(self._keys)
        
        # Log masked key for debugging
        masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "INVALID"
        logger.info(f"Using Groq Key Index {self._index}: {masked_key}")
        
        return key

    @property
    def key_count(self) -> int:
        return len(self._keys)

# Singleton instance
balancer = GroqBalancer()
