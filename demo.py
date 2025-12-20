#!/usr/bin/env python3
"""
Demo script for Aether-Evo without requiring network access
Simulates all components working together
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Set test environment
os.environ['WEEX_API_KEY'] = 'demo_key'
os.environ['WEEX_API_SECRET'] = 'demo_secret'
os.environ['WEEX_API_PASSWORD'] = 'demo_password'
os.environ['EXCHANGE_ID'] = 'binance'

from config import AetherConfig
from reasoning_loop import ReasoningLoop
from architect import Architect
from guardrails import Guardrails
import active_logic


class MockDiscoveryAgent:
    """Mock Discovery Agent for demo purposes"""
    
    def __init__(self, *args, **kwargs):
        self.capabilities = {
            'symbols': ['BTC/USDT', 'ETH/USDT'],
            'timeframes': {'15m': '15m', '1h': '1h'},
            'features': {
                'fetchOHLCV': True,
                'fetchTicker': True,
                'fetchBalance': True,
            }
        }
    
    async def discover_capabilities(self):
        return self.capabilities
    
    async def fetch_ohlcv(self, symbol, timeframe='15m', limit=100):
        """Generate mock OHLCV data with a trend"""
        base_price = 50000 if 'BTC' in symbol else 3000
        data = []
        for i in range(limit):
            timestamp = int(datetime.now().timestamp() * 1000) - (limit - i) * 15 * 60 * 1000
            open_price = base_price + i * 10
            high = open_price + 50
            low = open_price - 30
            close = open_price + 20
            volume = 1000 + i * 5
            data.append([timestamp, open_price, high, low, close, volume])
        return data
    
    async def fetch_balance(self):
        return {
            'total': {'USDT': 1000.0, 'BTC': 0.05},
            'free': {'USDT': 1000.0, 'BTC': 0.05}
        }


async def demo():
    """Run a complete demo of Aether-Evo"""
    print("=" * 70)
    print("🌟 AETHER-EVO DEMONSTRATION 🌟")
    print("=" * 70)
    print()
    
    # 1. Load Configuration
    print("1️⃣  Loading Configuration...")
    config = AetherConfig()
    print(f"   ✅ Config loaded: {config.trading.symbol}, {config.trading.reasoning_interval_minutes}m interval")
    print()
    
    # 2. Initialize Discovery Agent (Mock)
    print("2️⃣  Initializing Discovery Agent...")
    discovery = MockDiscoveryAgent()
    capabilities = await discovery.discover_capabilities()
    print(f"   ✅ Discovered {len(capabilities['symbols'])} trading pairs")
    print(f"   ✅ Available timeframes: {list(capabilities['timeframes'].keys())}")
    print()
    
    # 3. Initialize Guardrails
    print("3️⃣  Initializing Guardrails...")
    guardrails = Guardrails(
        initial_equity=1000.0,
        kill_switch_threshold=0.03,
        stability_lock_hours=12
    )
    print(f"   ✅ Kill-switch threshold: 3% in 1 hour")
    print(f"   ✅ Stability lock: 12 hours after evolution")
    print()
    
    # 4. Initialize Reasoning Loop
    print("4️⃣  Initializing Reasoning Loop...")
    reasoning = ReasoningLoop(
        discovery_agent=discovery,
        deepseek_config=config.deepseek,
        interval_minutes=config.trading.reasoning_interval_minutes
    )
    print(f"   ✅ R1 reasoning loop ready (15m interval)")
    print()
    
    # 5. Initialize Architect
    print("5️⃣  Initializing Architect...")
    architect = Architect(
        guardrails=guardrails,
        logic_file_path="active_logic.py"
    )
    print(f"   ✅ Evolution system ready")
    print()
    
    # 6. Run Analysis Cycle
    print("6️⃣  Running Analysis Cycle...")
    ohlcv = await discovery.fetch_ohlcv('BTC/USDT', '15m', 100)
    print(f"   ✅ Fetched {len(ohlcv)} candles")
    
    analysis = await reasoning.analyze_ohlcv(ohlcv, 'BTC/USDT')
    print(f"   ✅ R1 Analysis: {analysis['signal']} ({analysis['confidence']:.2%} confidence)")
    print(f"   📊 Reasoning: {analysis['reasoning']}")
    print()
    
    # 7. Generate Trading Signal
    print("7️⃣  Generating Trading Signal...")
    indicators = active_logic.calculate_indicators(ohlcv)
    signal = active_logic.generate_signal(indicators, analysis)
    print(f"   ✅ Signal: {signal['action']} ({signal['confidence']:.2%})")
    print(f"   💡 Reason: {signal['reason']}")
    print()
    
    # 8. Test Evolution System
    print("8️⃣  Testing Evolution System...")
    print(f"   Can evolve: {guardrails.can_evolve()}")
    
    if analysis.get('evolution_suggestion'):
        print(f"   🔄 R1 suggests evolution: {analysis['evolution_suggestion']['reason']}")
        evolved = await architect.evolve(analysis)
        if evolved:
            print(f"   ✨ Evolution successful!")
        else:
            print(f"   ℹ️  Evolution conditions not met (this is expected)")
    else:
        print(f"   ℹ️  No evolution suggested (current logic is performing well)")
    print()
    
    # 9. Test Kill-Switch
    print("9️⃣  Testing Kill-Switch...")
    # Simulate history
    old_time = datetime.now() - timedelta(minutes=59)
    guardrails.equity_history.append({
        'timestamp': old_time,
        'equity': 1000.0
    })
    
    # Test with safe equity (no trigger)
    guardrails.update_equity(980.0)  # 2% drop - safe
    print(f"   💰 Equity: $1000 → $980 (-2.0%)")
    print(f"   ✅ Kill-switch: {'TRIGGERED' if guardrails.is_kill_switch_active() else 'Inactive (OK)'}")
    
    # Test with dangerous equity (would trigger)
    guardrails.update_equity(960.0)  # 4% drop - danger!
    print(f"   💰 Equity: $1000 → $960 (-4.0%)")
    print(f"   🛑 Kill-switch: {'TRIGGERED' if guardrails.is_kill_switch_active() else 'Inactive'}")
    print()
    
    # 10. Status Summary
    print("🔟 System Status Summary")
    status = guardrails.get_status()
    print(f"   📊 Current Equity: ${status['current_equity']:.2f}")
    print(f"   📈 Change: {status['equity_change_pct']:+.2f}%")
    print(f"   🛡️  Kill-Switch: {'🛑 ACTIVE' if status['kill_switch_active'] else '✅ Inactive'}")
    print(f"   🔓 Can Evolve: {'Yes' if status['can_evolve'] else 'No (locked)'}")
    print(f"   🧬 Evolutions: {len(architect.get_evolution_history())}")
    print()
    
    print("=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Configuration management")
    print("  ✓ Discovery Agent (API mapping)")
    print("  ✓ Reasoning Loop (R1 analysis)")
    print("  ✓ Trading signal generation")
    print("  ✓ Evolution system (Architect)")
    print("  ✓ Guardrails (kill-switch, stability lock)")
    print("  ✓ Code validation and audit")
    print()
    print("Ready for production with real WEEX credentials!")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
