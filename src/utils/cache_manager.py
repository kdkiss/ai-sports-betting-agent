from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import asyncio
from functools import wraps
import hashlib

class CacheManager:
    """Manages caching of API responses and analysis results."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        
        # Default TTLs
        self.ttls = {
            'api_response': timedelta(hours=1),
            'weather_data': timedelta(hours=3),
            'news_data': timedelta(hours=1),
            'analysis': timedelta(minutes=30),
            'default': timedelta(hours=1)
        }
        
        # Cache locks to prevent race conditions
        self.locks: Dict[str, asyncio.Lock] = {}
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from prefix and data."""
        if isinstance(data, (str, bytes)):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
            
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return f"{prefix}_{hash_obj.hexdigest()}"
    
    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a cache key."""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        return self.locks[key]
    
    async def get(
        self,
        key: str,
        category: str = 'default'
    ) -> Tuple[Optional[Any], bool]:
        """Get value from cache if it exists and is not expired."""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None, False
            
        try:
            async with await self._get_lock(key):
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                    
                timestamp = datetime.fromisoformat(cached['timestamp'])
                ttl = self.ttls.get(category, self.ttls['default'])
                
                if datetime.now() - timestamp > ttl:
                    return None, False
                    
                return cached['data'], True
        except Exception as e:
            print(f"Error reading from cache: {e}")
            return None, False
    
    async def set(
        self,
        key: str,
        data: Any,
        category: str = 'default'
    ) -> None:
        """Store value in cache."""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            async with await self._get_lock(key):
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'category': category,
                        'data': data
                    }, f)
        except Exception as e:
            print(f"Error writing to cache: {e}")
    
    async def invalidate(self, key: str) -> None:
        """Remove item from cache."""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            async with await self._get_lock(key):
                if os.path.exists(cache_file):
                    os.remove(cache_file)
        except Exception as e:
            print(f"Error invalidating cache: {e}")
    
    def cached(self, prefix: str, category: str = 'default'):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key = self._get_cache_key(
                    prefix,
                    {'args': args, 'kwargs': kwargs}
                )
                
                # Try to get from cache
                cached_value, found = await self.get(key, category)
                if found:
                    return cached_value
                
                # Get fresh value
                value = await func(*args, **kwargs)
                
                # Store in cache
                await self.set(key, value, category)
                
                return value
            return wrapper
        return decorator
    
    async def cleanup(self, max_age: timedelta = timedelta(days=7)):
        """Clean up old cache files."""
        try:
            now = datetime.now()
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(self.cache_dir, filename)
                key = filename[:-5]  # Remove .json
                
                async with await self._get_lock(key):
                    try:
                        with open(filepath, 'r') as f:
                            cached = json.load(f)
                            timestamp = datetime.fromisoformat(
                                cached['timestamp']
                            )
                            
                            if now - timestamp > max_age:
                                os.remove(filepath)
                    except Exception as e:
                        print(f"Error cleaning up cache file {filepath}: {e}")
                        # Remove corrupted cache files
                        os.remove(filepath)
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'categories': {},
            'age_distribution': {
                'last_hour': 0,
                'last_day': 0,
                'last_week': 0,
                'older': 0
            }
        }
        
        try:
            now = datetime.now()
            
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(self.cache_dir, filename)
                stats['total_files'] += 1
                stats['total_size'] += os.path.getsize(filepath)
                
                try:
                    with open(filepath, 'r') as f:
                        cached = json.load(f)
                        category = cached.get('category', 'default')
                        timestamp = datetime.fromisoformat(
                            cached['timestamp']
                        )
                        
                        # Update category stats
                        if category not in stats['categories']:
                            stats['categories'][category] = 0
                        stats['categories'][category] += 1
                        
                        # Update age distribution
                        age = now - timestamp
                        if age <= timedelta(hours=1):
                            stats['age_distribution']['last_hour'] += 1
                        elif age <= timedelta(days=1):
                            stats['age_distribution']['last_day'] += 1
                        elif age <= timedelta(weeks=1):
                            stats['age_distribution']['last_week'] += 1
                        else:
                            stats['age_distribution']['older'] += 1
                except Exception as e:
                    print(f"Error reading cache file {filepath}: {e}")
        except Exception as e:
            print(f"Error getting cache stats: {e}")
        
        return stats 