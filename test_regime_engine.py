#!/usr/bin/env python3
"""
Test script for regime-aware native engine components
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data.regime import detect_regime, get_regime_metrics, ohlcv_list_to_dataframe, MarketRegime
from data.memory import EvolutionMemory
from core.weex_client import WEEXClient
import pandas as pd
import numpy as np


def test_regime_detection():
    """Test regime detection with synthetic data"""
    print("\n" + "="*60)
    print("TEST 1: Regime Detection")
    print("="*60)
    
    # Generate synthetic OHLCV data
    # Test 1: Trending Up
    timestamps = list(range(1000000000, 1000000000 + 100 * 60000, 60000))
    trending_up = []
    base_price = 100
    for i, ts in enumerate(timestamps):
        price = base_price + i * 0.5 + np.random.uniform(-0.1, 0.1)
        high = price + np.random.uniform(0, 0.5)
        low = price - np.random.uniform(0, 0.3)
        open_price = price + np.random.uniform(-0.2, 0.2)
        volume = 1000 + np.random.uniform(0, 500)
        trending_up.append([ts, open_price, high, low, price, volume])
    
    df_trending_up = ohlcv_list_to_dataframe(trending_up)
    regime_up = detect_regime(df_trending_up)
    metrics_up = get_regime_metrics(df_trending_up)
    
    print(f"\n✓ Trending Up Test:")
    print(f"  Regime: {regime_up}")
    print(f"  ADX: {metrics_up['adx']:.2f}")
    print(f"  +DI: {metrics_up['plus_di']:.2f}")
    print(f"  -DI: {metrics_up['minus_di']:.2f}")
    print(f"  ATR: {metrics_up['atr']:.4f}")
    print(f"  RSI: {metrics_up['rsi']:.2f}")
    
    # Test 2: Ranging Market (volatile)
    ranging = []
    for i, ts in enumerate(timestamps):
        price = base_price + np.sin(i * 0.1) * 5 + np.random.uniform(-2, 2)
        high = price + np.random.uniform(1, 3)
        low = price - np.random.uniform(1, 3)
        open_price = price + np.random.uniform(-1, 1)
        volume = 1000 + np.random.uniform(0, 1000)
        ranging.append([ts, open_price, high, low, price, volume])
    
    df_ranging = ohlcv_list_to_dataframe(ranging)
    regime_range = detect_regime(df_ranging)
    metrics_range = get_regime_metrics(df_ranging)
    
    print(f"\n✓ Ranging Market Test:")
    print(f"  Regime: {regime_range}")
    print(f"  ADX: {metrics_range['adx']:.2f}")
    print(f"  +DI: {metrics_range['plus_di']:.2f}")
    print(f"  -DI: {metrics_range['minus_di']:.2f}")
    print(f"  ATR: {metrics_range['atr']:.4f}")
    print(f"  RSI: {metrics_range['rsi']:.2f}")
    
    return True


def test_evolution_memory():
    """Test evolution memory management"""
    print("\n" + "="*60)
    print("TEST 2: Evolution Memory")
    print("="*60)
    
    # Use a test file
    test_file = "/tmp/test_evolution_history.json"
    memory = EvolutionMemory(history_file=test_file)
    
    # Test recording evolution
    print("\n✓ Recording evolution...")
    memory.record_evolution(
        parameters={'rsi_period': 14, 'adx_threshold': 25},
        reason='Low confidence in current logic',
        suggestion='Add regime-aware RSI',
        initial_equity=1000.0
    )
    
    stats = memory.get_statistics()
    print(f"  Total evolutions: {stats['total_evolutions']}")
    print(f"  Blacklisted parameters: {stats['blacklisted_parameters']}")
    
    # Test blacklisting
    print("\n✓ Testing blacklist...")
    test_params = {'rsi_period': 10, 'adx_threshold': 20}
    memory._blacklist_parameters(test_params, -50.0, 0)
    
    is_blacklisted, reason = memory.is_blacklisted(test_params)
    print(f"  Parameters blacklisted: {is_blacklisted}")
    print(f"  Reason: {reason}")
    
    # Test checking different parameters
    other_params = {'rsi_period': 14, 'adx_threshold': 25}
    is_blacklisted2, reason2 = memory.is_blacklisted(other_params)
    print(f"  Other parameters blacklisted: {is_blacklisted2}")
    
    stats = memory.get_statistics()
    print(f"\n  Final statistics:")
    print(f"    Total evolutions: {stats['total_evolutions']}")
    print(f"    Blacklisted parameters: {stats['blacklisted_parameters']}")
    print(f"    Success rate: {stats['success_rate']:.1f}%")
    
    return True


async def test_weex_client():
    """Test WEEX client (without actual API calls)"""
    print("\n" + "="*60)
    print("TEST 3: WEEX Native Client")
    print("="*60)
    
    # Test client initialization
    print("\n✓ Initializing WEEX client...")
    client = WEEXClient(
        api_key="test_key",
        api_secret="test_secret",
        api_password="test_password"
    )
    
    print("  Client initialized successfully")
    
    # Test precision enforcement with mock data
    print("\n✓ Testing precision enforcement...")
    
    # Mock market info
    client.market_info_cache['BTC-USDT'] = {
        'tick_size': Decimal('0.01'),
        'size_increment': Decimal('0.001'),
        'min_order_size': Decimal('0.001'),
        'max_order_size': Decimal('1000.0'),
        'contract_type': 'spot',
        'status': 'active'
    }
    
    # Test precision adjustment
    original_price = 50000.123456
    original_size = 0.123456789
    
    adjusted_price, adjusted_size = client._enforce_precision(
        'BTC-USDT',
        original_price,
        original_size
    )
    
    print(f"  Price adjustment: {original_price} -> {adjusted_price}")
    print(f"  Size adjustment: {original_size} -> {adjusted_size}")
    
    # Test validation
    is_valid = await client.validate_order_precision('BTC-USDT', 50000.12, 0.123)
    print(f"  Precision validation: {is_valid}")
    
    return True


def test_markdown_snapshot():
    """Test markdown snapshot formatting"""
    print("\n" + "="*60)
    print("TEST 4: Markdown Snapshot Formatting")
    print("="*60)
    
    from reasoning_loop import ReasoningLoop
    
    # Mock data
    ohlcv_data = [
        [1000000000, 100.0, 102.0, 99.0, 101.0, 1000],
        [1000060000, 101.0, 103.0, 100.5, 102.5, 1200],
    ]
    
    regime_metrics = {
        'regime': MarketRegime.TRENDING_UP,
        'adx': 30.5,
        'plus_di': 25.0,
        'minus_di': 15.0,
        'atr': 2.5,
        'rsi': 65.5
    }
    
    # Create mock reasoning loop
    reasoning = ReasoningLoop(
        discovery_agent=None,
        deepseek_config=None,
        interval_minutes=15
    )
    
    markdown = reasoning._format_markdown_snapshot(ohlcv_data, regime_metrics)
    
    print("\n✓ Markdown snapshot generated:")
    print(markdown)
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("REGIME-AWARE NATIVE ENGINE TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Regime Detection
        test_regime_detection()
        
        # Test 2: Evolution Memory
        test_evolution_memory()
        
        # Test 3: WEEX Client (async)
        asyncio.run(test_weex_client())
        
        # Test 4: Markdown Snapshot
        test_markdown_snapshot()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {str(e)}")
        print("="*60 + "\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
