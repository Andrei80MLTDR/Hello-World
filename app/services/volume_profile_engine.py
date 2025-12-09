from typing import List, Dict, Union, Tuple
from app.models.dto import Candle
import numpy as np


def safe_float(value) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except:
        return 0.0


def get_value(item: Union[Candle, Dict], key: str) -> float:
    """Extract float value from Candle or Dict."""
    if isinstance(item, dict):
        return safe_float(item.get(key, 0))
    else:
        return safe_float(getattr(item, key, 0))


def calculate_volume_profile(
    candles: Union[List[Candle], List[Dict]], 
    num_bins: int = 30,
    lookback_period: int = None
) -> Dict:
    """
    Calculate Volume Profile with POC, Value Area, and volume distribution.
    
    Args:
        candles: List of candle data
        num_bins: Number of price bins for volume distribution
        lookback_period: Number of candles to look back (None = all candles)
    
    Returns:
        Dictionary with:
        - poc: Point of Control (price with max volume)
        - vah: Value Area High (top of 70% volume)
        - val: Value Area Low (bottom of 70% volume)
        - volume_profile: Dict mapping price bins to volume
        - total_volume: Total volume in period
    """
    try:
        if not candles:
            return _empty_volume_profile()
        
        # Use lookback period if specified
        if lookback_period and len(candles) > lookback_period:
            candles = candles[-lookback_period:]
        
        if len(candles) < 10:
            return _empty_volume_profile()
        
        # Extract price and volume data
        highs = np.array([get_value(c, "high") for c in candles])
        lows = np.array([get_value(c, "low") for c in candles])
        closes = np.array([get_value(c, "close") for c in candles])
        volumes = np.array([get_value(c, "volume") for c in candles])
        
        # Calculate typical price for each candle
        typical_prices = (highs + lows + closes) / 3
        
        # Create price bins
        price_min = float(np.min(lows))
        price_max = float(np.max(highs))
        
        if price_min >= price_max or price_max == 0:
            return _empty_volume_profile()
        
        bins = np.linspace(price_min, price_max, num_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # Distribute volume across price bins
        volume_distribution = np.zeros(num_bins)
        
        for i, typical_price in enumerate(typical_prices):
            # Find which bin this price belongs to
            bin_idx = np.digitize(typical_price, bins) - 1
            bin_idx = max(0, min(num_bins - 1, bin_idx))  # Clamp to valid range
            
            # Weight volume across high-low range
            high_val = highs[i]
            low_val = lows[i]
            vol = volumes[i]
            
            # Distribute volume proportionally across bins that overlap with candle's range
            for j in range(num_bins):
                bin_low = bins[j]
                bin_high = bins[j + 1]
                
                # Check if this bin overlaps with candle's price range
                if bin_high >= low_val and bin_low <= high_val:
                    # Calculate overlap percentage
                    overlap_low = max(bin_low, low_val)
                    overlap_high = min(bin_high, high_val)
                    overlap = (overlap_high - overlap_low) / (high_val - low_val) if high_val > low_val else 1.0
                    volume_distribution[j] += vol * overlap
        
        # Find POC (Point of Control) - price with maximum volume
        poc_idx = int(np.argmax(volume_distribution))
        poc_price = float(bin_centers[poc_idx])
        
        # Calculate Value Area (70% of volume)
        total_volume = float(np.sum(volume_distribution))
        if total_volume == 0:
            return _empty_volume_profile()
        
        value_area_threshold = total_volume * 0.70
        
        # Start from POC and expand outward to capture 70% of volume
        value_area_volume = volume_distribution[poc_idx]
        lower_idx = poc_idx
        upper_idx = poc_idx
        
        while value_area_volume < value_area_threshold:
            # Check which direction to expand
            lower_vol = volume_distribution[lower_idx - 1] if lower_idx > 0 else 0
            upper_vol = volume_distribution[upper_idx + 1] if upper_idx < num_bins - 1 else 0
            
            if lower_vol == 0 and upper_vol == 0:
                break
            
            # Expand in direction with more volume
            if lower_vol > upper_vol and lower_idx > 0:
                lower_idx -= 1
                value_area_volume += lower_vol
            elif upper_idx < num_bins - 1:
                upper_idx += 1
                value_area_volume += upper_vol
            else:
                break
        
        vah = float(bin_centers[upper_idx])  # Value Area High
        val = float(bin_centers[lower_idx])  # Value Area Low
        
        # Create volume profile dictionary
        volume_profile_dict = {}
        for i, vol in enumerate(volume_distribution):
            if vol > 0:
                volume_profile_dict[float(bin_centers[i])] = float(vol)
        
        return {
            "poc": poc_price,
            "vah": vah,
            "val": val,
            "volume_profile": volume_profile_dict,
            "total_volume": total_volume,
            "num_bins": num_bins
        }
    
    except Exception as e:
        print(f"Error calculating volume profile: {e}")
        return _empty_volume_profile()


def _empty_volume_profile() -> Dict:
    """Return empty volume profile structure."""
    return {
        "poc": 0.0,
        "vah": 0.0,
        "val": 0.0,
        "volume_profile": {},
        "total_volume": 0.0,
        "num_bins": 0
    }


def is_price_in_value_area(price: float, vah: float, val: float) -> bool:
    """Check if price is within Value Area."""
    return val <= price <= vah


def is_price_near_poc(price: float, poc: float, threshold_pct: float = 0.02) -> bool:
    """Check if price is near POC within threshold percentage."""
    if poc == 0:
        return False
    return abs(price - poc) / poc <= threshold_pct


def get_volume_strength(current_volume: float, avg_volume: float) -> str:
    """
    Classify volume strength relative to average.
    
    Returns:
        "high": Volume > 1.5x average
        "normal": Volume between 0.5x and 1.5x average
        "low": Volume < 0.5x average
    """
    if avg_volume == 0:
        return "normal"
    
    ratio = current_volume / avg_volume
    
    if ratio > 1.5:
        return "high"
    elif ratio < 0.5:
        return "low"
    else:
        return "normal"
