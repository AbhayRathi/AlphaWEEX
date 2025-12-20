"""
Phase 3 Demo Script
Demonstrates all Phase 3 components working together
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.explorer import StochasticAlphaExplorer
from core.backtester import VectorizedBacktester
from data.logger import ReasoningLogger
from data.memory import EvolutionMemory
from config import AetherConfig


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


async def demo_phase3():
    """Demonstrate Phase 3 features"""
    print("\n" + "🌟" * 35)
    print("  AlphaWEEX Phase 3: The Alpha Factory & Reasoning Visualizer")
    print("🌟" * 35 + "\n")
    
    # Initialize components
    print("Initializing Phase 3 components...")
    config = AetherConfig()
    memory = EvolutionMemory()
    logger = ReasoningLogger()
    
    # 1. Stochastic Alpha Explorer Demo
    print_header("1. Stochastic Alpha Explorer - Creative Hypothesis Generation")
    
    explorer = StochasticAlphaExplorer(
        deepseek_config=config.deepseek,
        evolution_memory=memory,
        interval_hours=6,
        temperature=1.3
    )
    
    print("🔍 Exploring novel trading strategies with high creativity (temp=1.3)...")
    print("📊 Current regime: TRENDING_UP")
    print("🔬 Analyzing failed strategies to avoid repetition...\n")
    
    hypothesis = await explorer.explore(current_regime='TRENDING_UP')
    
    print("✨ NEW HYPOTHESIS GENERATED:")
    print(f"   {hypothesis['hypothesis']}")
    print(f"\n📈 Confidence: {hypothesis['confidence']:.0%}")
    print(f"🎯 Suggested Indicators:")
    for indicator in hypothesis['suggested_indicators']:
        print(f"      • {indicator}")
    print(f"\n💡 Implementation Hints:")
    for i, hint in enumerate(hypothesis['implementation_hints'], 1):
        print(f"      {i}. {hint}")
    
    # Log hypothesis
    logger.log_hypothesis(hypothesis, source='explorer')
    
    # 2. Vectorized Backtester Demo
    print_header("2. Vectorized Backtester - Strategy Validation")
    
    backtester = VectorizedBacktester()
    
    print("🔬 Running backtest on current active_logic.py...")
    print("📊 Using 1000 candles of historical data")
    print("⚖️  Deployment thresholds: Sharpe > 1.2, Max DD < 5%\n")
    
    result = backtester.run_backtest(initial_capital=10000.0)
    
    if result['success']:
        metrics = result['metrics']
        
        print("📈 BACKTEST RESULTS:")
        print(f"   Total Return:  {metrics['total_return']:>8.2%}")
        print(f"   Sharpe Ratio:  {metrics['sharpe_ratio']:>8.2f} {'✅' if metrics['sharpe_ratio'] > 1.2 else '❌'}")
        print(f"   Max Drawdown:  {metrics['max_drawdown']:>8.2%} {'✅' if metrics['max_drawdown'] < 0.05 else '❌'}")
        print(f"   Win Rate:      {metrics['win_rate']:>8.2%}")
        print(f"   Num Trades:    {metrics['num_trades']:>8}")
        print(f"   Final Equity:  ${metrics['final_equity']:>8.2f}")
        
        print(f"\n{'✅' if result['can_deploy'] else '❌'} Deployment Status: {'APPROVED' if result['can_deploy'] else 'BLOCKED'}")
        
        if not result['can_deploy']:
            print("   Strategy does not meet deployment criteria")
            print("   Evolution will be blocked until strategy improves")
    
    # 3. Reasoning Logger Demo
    print_header("3. Reasoning Logger - Complete Trace Logging")
    
    # Create sample analysis
    sample_analysis = {
        'signal': 'BUY',
        'confidence': 0.78,
        'regime': 'TRENDING_UP',
        'reasoning': 'Strong uptrend with volume confirmation and RSI support',
        'r1_prompt': 'Analyze current market conditions...',
        'metrics': {
            'price': 45000,
            'rsi': 65.5,
            'volume_spike': True
        }
    }
    
    print("📝 Logging reasoning trace...")
    logger.log_analysis(sample_analysis, source='reasoning_loop')
    
    print("✅ Reasoning trace saved to data/reasoning_logs.jsonl")
    
    # Show statistics
    stats = logger.get_statistics()
    print(f"\n📊 Logger Statistics:")
    print(f"   Total traces:  {stats['total_traces']}")
    print(f"   File size:     {stats['file_size_mb']:.3f} MB")
    print(f"   Sources:")
    for source, count in stats['sources'].items():
        print(f"      • {source}: {count} traces")
    
    # Show recent traces
    print("\n📖 Recent Traces:")
    traces = logger.read_recent_traces(count=3)
    for i, trace in enumerate(traces[-3:], 1):
        print(f"   {i}. [{trace['source']}] {trace['timestamp'][:19]} - {trace['thought_count']} thoughts")
    
    # 4. Dashboard Preview
    print_header("4. Interactive Dashboard - System Visualization")
    
    print("🖥️  Dashboard Features:")
    print("   • Thinking Log - Real-time R1 reasoning with <thought> tags")
    print("   • Strategy Lineage - Visual evolution timeline")
    print("   • Live Metrics - PnL tracking vs kill-switch threshold")
    print("   • System Status - Component health monitoring")
    
    print("\n🚀 To launch the dashboard, run:")
    print("   streamlit run dashboard/app.py")
    print("\n   Then open your browser to: http://localhost:8501")
    
    # Summary
    print_header("Summary - Phase 3 Components Working")
    
    print("✅ Stochastic Alpha Explorer")
    print("   • 6-hour creative hypothesis generation")
    print("   • Temperature 1.3 for unconventional ideas")
    print("   • Analyzes failed strategies to avoid repetition")
    
    print("\n✅ Vectorized Backtester")
    print("   • Pandas-based for speed")
    print("   • Sharpe Ratio & Max Drawdown validation")
    print("   • Blocks deployment if thresholds not met")
    
    print("\n✅ Reasoning Logger")
    print("   • JSONL format for easy parsing")
    print("   • <thought> tag extraction")
    print("   • Automatic log rotation at 100MB")
    
    print("\n✅ Interactive Dashboard")
    print("   • Streamlit-based web interface")
    print("   • Real-time visualization")
    print("   • Multiple views (Thinking, Lineage, Metrics)")
    
    print("\n" + "=" * 70)
    print("  🎉 Phase 3 Implementation Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_phase3())
