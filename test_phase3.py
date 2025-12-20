"""
Integration test for Phase 3 components
Tests Explorer, Backtester, Logger, and Dashboard components
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.explorer import StochasticAlphaExplorer
from core.backtester import VectorizedBacktester
from data.logger import ReasoningLogger
from data.memory import EvolutionMemory
from config import AetherConfig


async def test_explorer():
    """Test Stochastic Alpha Explorer"""
    print("=" * 60)
    print("Testing Stochastic Alpha Explorer")
    print("=" * 60)
    
    config = AetherConfig()
    memory = EvolutionMemory()
    
    explorer = StochasticAlphaExplorer(
        deepseek_config=config.deepseek,
        evolution_memory=memory,
        interval_hours=6,
        temperature=1.3
    )
    
    # Test exploration
    hypothesis = await explorer.explore(current_regime='TRENDING_UP')
    
    print(f"✅ Hypothesis Generated:")
    print(f"   Regime: {hypothesis['regime']}")
    print(f"   Hypothesis: {hypothesis['hypothesis']}")
    print(f"   Confidence: {hypothesis['confidence']:.2%}")
    print(f"   Indicators: {', '.join(hypothesis['suggested_indicators'])}")
    print()
    
    return True


def test_backtester():
    """Test Vectorized Backtester"""
    print("=" * 60)
    print("Testing Vectorized Backtester")
    print("=" * 60)
    
    backtester = VectorizedBacktester()
    
    # Run backtest
    result = backtester.run_backtest()
    
    print(f"✅ Backtest Complete:")
    print(f"   Success: {result['success']}")
    print(f"   Can Deploy: {result['can_deploy']}")
    
    if result['success']:
        metrics = result['metrics']
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"   Total Return: {metrics['total_return']:.2%}")
        print(f"   Num Trades: {metrics['num_trades']}")
    print()
    
    return result['success']


def test_logger():
    """Test Reasoning Logger"""
    print("=" * 60)
    print("Testing Reasoning Logger")
    print("=" * 60)
    
    logger = ReasoningLogger()
    
    # Test logging analysis
    analysis = {
        'signal': 'BUY',
        'confidence': 0.75,
        'regime': 'TRENDING_UP',
        'reasoning': 'Test reasoning',
        'r1_prompt': 'Test prompt',
        'metrics': {}
    }
    
    logger.log_analysis(analysis, source='test')
    
    # Test logging hypothesis
    hypothesis = {
        'hypothesis': 'Test hypothesis',
        'confidence': 0.65,
        'regime': 'TRENDING_UP',
        'temperature': 1.3,
        'suggested_indicators': ['RSI'],
        'implementation_hints': ['Test hint'],
        'failed_strategies_analyzed': 0
    }
    
    logger.log_hypothesis(hypothesis, source='test')
    
    # Read traces
    traces = logger.read_recent_traces(count=2)
    
    print(f"✅ Logger Working:")
    print(f"   Traces logged: {len(traces)}")
    
    stats = logger.get_statistics()
    print(f"   Total traces: {stats['total_traces']}")
    print(f"   File size: {stats['file_size_mb']:.2f} MB")
    print()
    
    return len(traces) >= 2


def test_dashboard_import():
    """Test Dashboard can be imported"""
    print("=" * 60)
    print("Testing Dashboard Import")
    print("=" * 60)
    
    try:
        from dashboard import app
        print("✅ Dashboard imports successfully")
        print("   Run with: streamlit run dashboard/app.py")
        print()
        return True
    except Exception as e:
        print(f"❌ Dashboard import failed: {str(e)}")
        print()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 AlphaWEEX Phase 3 Integration Tests")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test Explorer
    try:
        results['explorer'] = await test_explorer()
    except Exception as e:
        print(f"❌ Explorer test failed: {str(e)}\n")
        results['explorer'] = False
    
    # Test Backtester
    try:
        results['backtester'] = test_backtester()
    except Exception as e:
        print(f"❌ Backtester test failed: {str(e)}\n")
        results['backtester'] = False
    
    # Test Logger
    try:
        results['logger'] = test_logger()
    except Exception as e:
        print(f"❌ Logger test failed: {str(e)}\n")
        results['logger'] = False
    
    # Test Dashboard
    try:
        results['dashboard'] = test_dashboard_import()
    except Exception as e:
        print(f"❌ Dashboard test failed: {str(e)}\n")
        results['dashboard'] = False
    
    # Print summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {component.capitalize()}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print("🎉 All Phase 3 components working correctly!")
    else:
        print("⚠️  Some tests failed. Check output above for details.")
    
    print()
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
