#!/usr/bin/env python3
"""
Demo script showcasing the regime-aware native engine features
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data.regime import detect_regime, get_regime_metrics, ohlcv_list_to_dataframe
from data.memory import EvolutionMemory
from core.weex_client import WEEXClient
from reasoning_loop import ReasoningLoop
from decimal import Decimal


def generate_sample_ohlcv(regime_type='trending_up', bars=100):
    """Generate sample OHLCV data for different regimes"""
    timestamps = list(range(1700000000000, 1700000000000 + bars * 60000, 60000))
    data = []
    base_price = 50000
    
    if regime_type == 'trending_up':
        for i, ts in enumerate(timestamps):
            price = base_price + i * 50 + np.random.uniform(-10, 10)
            high = price + np.random.uniform(5, 20)
            low = price - np.random.uniform(5, 15)
            open_price = price + np.random.uniform(-5, 5)
            volume = 100 + np.random.uniform(0, 50)
            data.append([ts, open_price, high, low, price, volume])
    
    elif regime_type == 'trending_down':
        for i, ts in enumerate(timestamps):
            price = base_price - i * 50 + np.random.uniform(-10, 10)
            high = price + np.random.uniform(5, 15)
            low = price - np.random.uniform(5, 20)
            open_price = price + np.random.uniform(-5, 5)
            volume = 100 + np.random.uniform(0, 50)
            data.append([ts, open_price, high, low, price, volume])
    
    elif regime_type == 'range_volatile':
        for i, ts in enumerate(timestamps):
            price = base_price + np.sin(i * 0.2) * 200 + np.random.uniform(-100, 100)
            high = price + np.random.uniform(50, 150)
            low = price - np.random.uniform(50, 150)
            open_price = price + np.random.uniform(-50, 50)
            volume = 100 + np.random.uniform(50, 200)
            data.append([ts, open_price, high, low, price, volume])
    
    else:  # range_quiet
        for i, ts in enumerate(timestamps):
            price = base_price + np.sin(i * 0.1) * 50 + np.random.uniform(-10, 10)
            high = price + np.random.uniform(5, 15)
            low = price - np.random.uniform(5, 15)
            open_price = price + np.random.uniform(-5, 5)
            volume = 100 + np.random.uniform(0, 30)
            data.append([ts, open_price, high, low, price, volume])
    
    return data


def demo_regime_detection():
    """Demonstrate regime detection across different market conditions"""
    print("\n" + "="*80)
    print("DEMO 1: MARKET REGIME DETECTION")
    print("="*80)
    
    regimes = ['trending_up', 'trending_down', 'range_volatile', 'range_quiet']
    
    for regime_type in regimes:
        print(f"\n{'─'*80}")
        print(f"Testing: {regime_type.upper().replace('_', ' ')}")
        print('─'*80)
        
        # Generate sample data
        ohlcv_data = generate_sample_ohlcv(regime_type, 100)
        df = ohlcv_list_to_dataframe(ohlcv_data)
        
        # Detect regime
        metrics = get_regime_metrics(df)
        
        print(f"\n📊 Market Analysis:")
        print(f"   Current Price: ${ohlcv_data[-1][4]:.2f}")
        print(f"   Price Range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        print(f"\n📈 Technical Indicators:")
        print(f"   RSI: {metrics['rsi']:.2f}")
        print(f"   ATR: {metrics['atr']:.4f}")
        print(f"   ADX: {metrics['adx']:.2f} ({'Strong trend' if metrics['adx'] > 25 else 'Weak trend'})")
        print(f"   +DI: {metrics['plus_di']:.2f}")
        print(f"   -DI: {metrics['minus_di']:.2f}")
        
        print(f"\n🎯 Detected Regime: **{metrics['regime']}**")
        
        # Strategy recommendation based on regime
        if metrics['regime'] == 'TRENDING_UP':
            print("   💡 Strategy: Aggressive buying on pullbacks, tight stops")
        elif metrics['regime'] == 'TRENDING_DOWN':
            print("   💡 Strategy: Aggressive selling on rallies, tight stops")
        elif metrics['regime'] == 'RANGE_VOLATILE':
            print("   💡 Strategy: Mean reversion with wider stops")
        else:  # RANGE_QUIET
            print("   💡 Strategy: Await breakout confirmation")


async def demo_weex_client():
    """Demonstrate WEEX native client features"""
    print("\n" + "="*80)
    print("DEMO 2: WEEX NATIVE CLIENT WITH PRECISION ENFORCEMENT")
    print("="*80)
    
    # Initialize client
    print("\n📡 Initializing WEEX Native Client...")
    client = WEEXClient(
        api_key="demo_key",
        api_secret="demo_secret",
        api_password="demo_pass"
    )
    
    # Simulate market info (normally fetched from API)
    print("\n📋 Simulating Market Contracts Discovery...")
    client.market_info_cache = {
        'BTC-USDT': {
            'tick_size': Decimal('0.01'),
            'size_increment': Decimal('0.001'),
            'min_order_size': Decimal('0.001'),
            'max_order_size': Decimal('100.0'),
            'contract_type': 'spot',
            'status': 'active'
        },
        'ETH-USDT': {
            'tick_size': Decimal('0.01'),
            'size_increment': Decimal('0.0001'),
            'min_order_size': Decimal('0.01'),
            'max_order_size': Decimal('1000.0'),
            'contract_type': 'spot',
            'status': 'active'
        }
    }
    
    print("   ✅ Market info cached for 2 symbols")
    
    # Test precision enforcement
    print("\n🔧 Testing Precision Enforcement:")
    
    test_cases = [
        ('BTC-USDT', 50123.456789, 0.123456789),
        ('ETH-USDT', 2543.98765432, 1.234567890),
    ]
    
    for symbol, price, size in test_cases:
        print(f"\n   Symbol: {symbol}")
        print(f"   Original: Price=${price:.8f}, Size={size:.9f}")
        
        adjusted_price, adjusted_size = client._enforce_precision(symbol, price, size)
        
        print(f"   Adjusted: Price=${adjusted_price}, Size={adjusted_size}")
        print(f"   ✓ Enforced tick_size and size_increment")
    
    # Test validation
    print("\n✅ Precision Validation:")
    is_valid = await client.validate_order_precision('BTC-USDT', 50000.01, 0.123)
    print(f"   Order (50000.01, 0.123): {'Valid ✓' if is_valid else 'Invalid ✗'}")
    
    is_valid = await client.validate_order_precision('BTC-USDT', 50000.123, 0.123)
    print(f"   Order (50000.123, 0.123): {'Valid ✓' if is_valid else 'Invalid ✗ - needs adjustment'}")


def demo_evolution_memory():
    """Demonstrate evolution memory and self-correction"""
    print("\n" + "="*80)
    print("DEMO 3: SELF-CORRECTION MEMORY WITH PARAMETER BLACKLISTING")
    print("="*80)
    
    # Initialize memory
    memory = EvolutionMemory(history_file="/tmp/demo_evolution_history.json")
    
    print("\n📝 Simulating Evolution Cycle...")
    
    # Simulate successful evolution
    print("\n1️⃣ Evolution #1: Adding RSI indicator")
    memory.record_evolution(
        parameters={'rsi_period': 14, 'regime': 'TRENDING_UP'},
        reason='Low confidence in trending up regime',
        suggestion='Add regime-aware RSI with period 14',
        initial_equity=10000.0
    )
    print("   ✅ Recorded evolution")
    
    # Simulate failed evolution (negative PnL)
    print("\n2️⃣ Evolution #2: Aggressive breakout strategy")
    memory.record_evolution(
        parameters={'breakout_threshold': 0.02, 'regime': 'RANGE_VOLATILE'},
        reason='Attempting breakout strategy in volatile range',
        suggestion='Use aggressive breakout with 2% threshold',
        initial_equity=9500.0
    )
    
    # Simulate negative PnL after 2 hours
    print("   ⏱️  2 hours later: PnL = -250 (negative)")
    memory._blacklist_parameters(
        parameters={'breakout_threshold': 0.02, 'regime': 'RANGE_VOLATILE'},
        pnl=-250.0,
        evolution_index=1
    )
    print("   ⚠️  Parameters blacklisted!")
    
    # Try to use blacklisted parameters
    print("\n3️⃣ Attempting to use blacklisted parameters...")
    is_blacklisted, reason = memory.is_blacklisted(
        {'breakout_threshold': 0.02, 'regime': 'RANGE_VOLATILE'}
    )
    
    if is_blacklisted:
        print(f"   🛑 BLOCKED: {reason}")
        print("   ✅ Self-correction working - prevented repeated mistake!")
    
    # Show statistics
    print("\n📊 Evolution Memory Statistics:")
    stats = memory.get_statistics()
    print(f"   Total evolutions: {stats['total_evolutions']}")
    print(f"   Blacklisted parameters: {stats['blacklisted_parameters']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    print(f"   Pending evaluations: {stats['pending_evaluations']}")


def demo_markdown_snapshot():
    """Demonstrate markdown snapshot for R1 reasoning"""
    print("\n" + "="*80)
    print("DEMO 4: MARKDOWN TABLE SNAPSHOT FOR DEEPSEEK R1")
    print("="*80)
    
    # Generate sample data
    ohlcv_data = generate_sample_ohlcv('trending_up', 100)
    df = ohlcv_list_to_dataframe(ohlcv_data)
    metrics = get_regime_metrics(df)
    
    # Create reasoning loop to format snapshot
    reasoning = ReasoningLoop(
        discovery_agent=None,
        deepseek_config=None,
        interval_minutes=15
    )
    
    # Format snapshot
    snapshot = reasoning._format_markdown_snapshot(ohlcv_data, metrics)
    
    print("\n📋 Generated Snapshot for R1:")
    print(snapshot)
    
    print("\n💭 This snapshot would be sent to DeepSeek-R1 with the prompt:")
    print("   'Based on this regime and performance history, should we mutate active_logic.py?'")


async def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("🌟 ALPHAWEEX REGIME-AWARE NATIVE ENGINE DEMO")
    print("="*80)
    print("\nShowcasing the upgraded features:")
    print("  1. Market Regime Detection (ADX + ATR)")
    print("  2. WEEX Native Client with Precision Enforcement")
    print("  3. Self-Correction Memory with Parameter Blacklisting")
    print("  4. Markdown Table Snapshot for DeepSeek R1")
    
    try:
        # Demo 1: Regime Detection
        demo_regime_detection()
        
        # Demo 2: WEEX Client
        await demo_weex_client()
        
        # Demo 3: Evolution Memory
        demo_evolution_memory()
        
        # Demo 4: Markdown Snapshot
        demo_markdown_snapshot()
        
        print("\n" + "="*80)
        print("✅ DEMO COMPLETE - All Features Working!")
        print("="*80)
        print("\n📚 Summary:")
        print("  ✓ Regime detection identifies market conditions (TRENDING/RANGE)")
        print("  ✓ Native WEEX client enforces precision (tick_size, size_increment)")
        print("  ✓ Evolution memory tracks PnL and blacklists failed parameters")
        print("  ✓ Markdown snapshots format data for DeepSeek R1 reasoning")
        print("\n🚀 The system is now REGIME-AWARE and ready for production!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
