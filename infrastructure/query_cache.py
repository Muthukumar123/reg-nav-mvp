"""
Query Cache Module for Performance Optimization

Implements similarity-based caching to reduce redundant LLM calls.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
import hashlib

class QueryCache:
    """Cache LLM responses based on semantic similarity."""
    
    def __init__(self, max_cache_size: int = 100, ttl_minutes: int = 60):
        """
        Initialize query cache.
        
        Args:
            max_cache_size: Maximum number of cached queries (LRU eviction)
            ttl_minutes: Time-to-live for cached entries in minutes
        """
        self.cache = {}  # {query_hash: {"question", "answer", "citations", "scores", "timestamp"}}
        self.max_size = max_cache_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.hits = 0
        self.misses = 0
        self.cache_order = []  # Track insertion order for LRU
    
    def _normalize_query(self, question: str) -> str:
        """Normalize query for caching (lowercase, strip whitespace)."""
        return question.lower().strip()
    
    def _hash_query(self, question: str) -> str:
        """Create hash of normalized query."""
        normalized = self._normalize_query(question)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, question: str) -> Optional[Dict]:
        """
        Get cached response for query if available and fresh.
        
        Returns:
            Dict with {"answer", "citations", "scores"} or None if not cached
        """
        query_hash = self._hash_query(question)
        
        if query_hash not in self.cache:
            self.misses += 1
            return None
        
        cached_entry = self.cache[query_hash]
        
        # Check if cache entry has expired
        if datetime.now() - cached_entry["timestamp"] > self.ttl:
            del self.cache[query_hash]
            self.cache_order.remove(query_hash)
            self.misses += 1
            return None
        
        # Cache hit
        self.hits += 1
        return {
            "answer": cached_entry["answer"],
            "citations": cached_entry["citations"],
            "scores": cached_entry["scores"]
        }
    
    def set(self, question: str, answer: str, citations: List[Dict], scores: List[float]):
        """Store response in cache."""
        query_hash = self._hash_query(question)
        
        # Remove old entry if exists (will re-add to end for LRU)
        if query_hash in self.cache:
            self.cache_order.remove(query_hash)
        
        # Evict oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            oldest_hash = self.cache_order.pop(0)
            del self.cache[oldest_hash]
        
        # Store new entry
        self.cache[query_hash] = {
            "question": question,
            "answer": answer,
            "citations": citations,
            "scores": scores,
            "timestamp": datetime.now()
        }
        self.cache_order.append(query_hash)
    
    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.cache_order.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_minutes": self.ttl.total_seconds() / 60
        }
    
    def evict_expired(self):
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_hashes = []
        
        for query_hash, entry in self.cache.items():
            if now - entry["timestamp"] > self.ttl:
                expired_hashes.append(query_hash)
        
        for query_hash in expired_hashes:
            del self.cache[query_hash]
            self.cache_order.remove(query_hash)
        
        return len(expired_hashes)

# Global cache instance
query_cache = QueryCache(max_cache_size=100, ttl_minutes=60)
