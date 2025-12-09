import json
import time
from pathlib import Path
from typing import Optional, List, Callable

class KlinesCache:
    """Cache layer pentru klines Binance - evita rate limiting"""
    
    def __init__(self, cache_dir: str = ".cache/klines"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, symbol: str, interval: str) -> Path:
        return self.cache_dir / f"{symbol}_{interval}.json"
    
    def get(self, symbol: str, interval: str, max_age_hours: int = 24) -> Optional[List]:
        """Returnează cached klines dacă sunt freshe"""
        cache_path = self._get_cache_path(symbol, interval)
        
        if not cache_path.exists():
            return None
        
        file_age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        if file_age_hours > max_age_hours:
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(self, symbol: str, interval: str, data: List) -> None:
        """Salvează klines în cache"""
        cache_path = self._get_cache_path(symbol, interval)
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            print(f"Cache write error: {e}")
    
    def clear(self, symbol: Optional[str] = None) -> None:
        """Șterge cache"""
        if symbol:
            for f in self.cache_dir.glob(f"{symbol}_*.json"):
                f.unlink(missing_ok=True)
        else:
            for f in self.cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)


_cache_instance = KlinesCache()

def get_or_cache_klines(
    symbol: str,
    interval: str,
    fetch_fn: Callable[[], List],
    max_age_hours: int = 24
) -> List:
    """Încercă cache, dacă fail fetch și salvează"""
    cached = _cache_instance.get(symbol, interval, max_age_hours)
    if cached is not None:
        return cached
    
    data = fetch_fn()
    _cache_instance.set(symbol, interval, data)
    return data
