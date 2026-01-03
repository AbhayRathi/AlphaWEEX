"""
Predator Suite Demo - Demonstrates the three core agents

This script showcases:
1. BehavioralAdversary - Psychological analysis
2. ReconciliationAuditor - Prediction tracking and validation
3. EvolutionaryMutator - Self-improvement through prompt evolution
"""
import asyncio
import time
from datetime import datetime

from agents.adversary import BehavioralAdversary
from agents.reconciliation_loop import IntelligenceLedger, ReconciliationAuditor
from agents.evolutionary_mutator import EvolutionaryMutator


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


async def demo_behavioral_adversary():
    """Demo: BehavioralAdversary - The Dark Mirror"""
    print_section("AGENT 1: BEHAVIORAL ADVERSARY")
    
    # Initialize with Shadow Mode (for demo without API key)
    adversary = BehavioralAdversary(use_shadow_mode=True)
    
    # Scenario 1: Flash Crash (Panic Seller Detection)
    print("\n📊 Scenario 1: Flash Crash (-5% drop)")
    market_data = {
        'price': 85500.0,
        'rsi': 20.0,
        'volume': 5000.0,
        'price_change_pct': -5.0,
        'recent_lows': [86000, 87000, 88000]
    }
    
    result = adversary.analyze_psychology(market_data, sentiment="Extreme Fear")
    
    print(f"  Detected: {result['detected_archetype']}")
    print(f"  Signal: {result['signal']}")
    print(f"  Outcome: {result['predicted_outcome']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Reasoning: {result['reasoning'][:80]}...")
    
    # Scenario 2: FOMO Chaser (Bull Trap)
    print("\n📊 Scenario 2: Vertical Move (+5.5%)")
    market_data = {
        'price': 95000.0,
        'rsi': 78.0,
        'volume': 8000.0,
        'price_change_pct': 5.5,
    }
    
    result = adversary.analyze_psychology(market_data, sentiment="Extreme Greed")
    
    print(f"  Detected: {result['detected_archetype']}")
    print(f"  Signal: {result['signal']}")
    print(f"  Outcome: {result['predicted_outcome']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    
    # Liquidity Zones
    print(f"\n💧 Predicted Liquidity Zones (Stop-Loss Clusters):")
    for i, zone in enumerate(result['liquidity_zones'][:3], 1):
        print(f"    {i}. ${zone:,.2f}")
    
    return adversary, result


async def demo_reconciliation_auditor(adversary):
    """Demo: ReconciliationAuditor - The Auditor"""
    print_section("AGENT 2: RECONCILIATION AUDITOR")
    
    # Initialize
    ledger = IntelligenceLedger(db_path="data/demo_ledger.db")
    auditor = ReconciliationAuditor(ledger=ledger)
    
    print("\n📝 Recording 3 predictions...")
    
    # Record 3 predictions with different outcomes
    predictions = [
        {
            'data': {'price': 95000, 'rsi': 78, 'price_change_pct': 5.5},
            'sentiment': 'Greed',
            'actual_1h': 93000,  # Correct prediction (went down)
            'label': 'FOMO Bull Trap'
        },
        {
            'data': {'price': 85000, 'rsi': 22, 'price_change_pct': -5},
            'sentiment': 'Fear',
            'actual_1h': 87000,  # Correct prediction (went up)
            'label': 'Panic Mean Reversion'
        },
        {
            'data': {'price': 90000, 'rsi': 50, 'price_change_pct': 0},
            'sentiment': 'Neutral',
            'actual_1h': 88000,  # Wrong prediction (unexpected drop)
            'label': 'Neutral Hold'
        }
    ]
    
    pred_ids = []
    for i, pred in enumerate(predictions, 1):
        result = adversary.analyze_psychology(pred['data'], sentiment=pred['sentiment'])
        
        pred_id = ledger.record_prediction(
            predicted_bias=result['predicted_bias'],
            predicted_outcome=result['predicted_outcome'],
            confidence=result['confidence'],
            market_regime=result['market_regime'],
            archetype=result['detected_archetype'],
            signal=result['signal'],
            price_at_prediction=pred['data']['price']
        )
        pred_ids.append(pred_id)
        
        print(f"  {i}. {pred['label']}: Predicted {result['signal']} @ ${pred['data']['price']:,}")
    
    # Simulate audit after 1 hour
    print("\n🔍 Running 1-hour audit...")
    await asyncio.sleep(0.1)  # Simulate time passing
    
    for i, (pred_id, pred) in enumerate(zip(pred_ids, predictions), 1):
        # Update actual price
        ledger.update_actual_price(pred_id, pred['actual_1h'], "1h")
        
        # Calculate score
        prediction_data = {
            'id': pred_id,
            'predicted_bias': 'Test',
            'predicted_outcome': predictions[i-1]['label'],
            'confidence': 0.7,
            'signal': 'SELL' if i == 1 else 'BUY' if i == 2 else 'HOLD',
            'price_at_prediction': pred['data']['price']
        }
        
        score = auditor._calculate_success_score(prediction_data, pred['actual_1h'])
        ledger.update_success_score(pred_id, "1h", score)
        
        outcome = "✅ Correct" if score > 0 else "❌ Wrong"
        print(f"  {i}. Prediction #{pred_id}: {outcome} (Score: {score:+.2f})")
    
    # Display statistics
    stats = ledger.get_statistics()
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Predictions: {stats['total_predictions']}")
    print(f"  Average Score (1h): {stats['avg_score_1h']:.2f}")
    
    # Get failed predictions
    failed = ledger.get_failed_predictions(limit=5)
    if failed:
        print(f"\n❌ Failed Predictions for Learning: {len(failed)}")
        for fail in failed[:2]:
            print(f"  - {fail['predicted_bias']} (Score: {fail.get('avg_score', 0):.2f})")
    
    return ledger, auditor, failed


async def demo_evolutionary_mutator(failed_predictions):
    """Demo: EvolutionaryMutator - The DNA Patch"""
    print_section("AGENT 3: EVOLUTIONARY MUTATOR")
    
    # Initialize
    mutator = EvolutionaryMutator(
        prompts_dir="data/demo_prompts",
        evolution_interval_hours=24
    )
    
    print(f"\n🧬 Current Prompt Version: v{mutator.current_version}")
    
    # Display current prompt (first 200 chars)
    current_prompt = mutator.load_current_prompt()
    print(f"\n📄 Current System Prompt Preview:")
    print(f"  {current_prompt[:200]}...")
    
    # Test Symmetry Guard
    print(f"\n🛡️  Testing Symmetry Guard...")
    
    safe_prompt = """
    You are a behavioral analyst.
    Always use stop-losses and risk management.
    Explain your reasoning step-by-step.
    """
    
    dangerous_prompt = """
    You are a trader.
    No stop-losses needed.
    Go all in on every trade.
    """
    
    safe_result = mutator._symmetry_guard(safe_prompt)
    dangerous_result = mutator._symmetry_guard(dangerous_prompt)
    
    print(f"  Safe prompt: {'✅ Passed' if safe_result else '❌ Rejected'}")
    print(f"  Dangerous prompt: {'✅ Passed' if dangerous_result else '❌ Rejected'}")
    
    # Mock evolution (won't actually evolve without API key)
    if failed_predictions:
        print(f"\n🔄 Attempting evolution with {len(failed_predictions)} failed predictions...")
        print(f"  (Would analyze failures and evolve prompt in production)")
        
        # This will skip evolution without API, but shows the flow
        new_prompt = mutator.evolve_prompt(failed_predictions, force=False)
        
        if new_prompt:
            print(f"  ✅ Evolved to v{mutator.current_version}")
        else:
            print(f"  ℹ️  Evolution skipped (requires API key or 24h interval)")
    
    # Show evolution history
    history = mutator.get_evolution_history()
    print(f"\n📚 Evolution History: {len(history)} versions")
    for v in history[:3]:
        print(f"  v{v['version']}: Created {v['created'][:19]}")
    
    return mutator


async def main():
    """Run the complete Predator Suite demo"""
    print("╔" + "═"*58 + "╗")
    print("║" + " "*10 + "AETHER-EVO PREDATOR SUITE DEMO" + " "*18 + "║")
    print("║" + " "*16 + "Behavioral Analysis & Self-Evolution" + " "*6 + "║")
    print("╚" + "═"*58 + "╝")
    
    start_time = time.time()
    
    # Demo each agent
    adversary, last_analysis = await demo_behavioral_adversary()
    await asyncio.sleep(0.5)
    
    ledger, auditor, failed = await demo_reconciliation_auditor(adversary)
    await asyncio.sleep(0.5)
    
    mutator = await demo_evolutionary_mutator(failed)
    
    # Summary
    print_section("DEMO COMPLETE")
    elapsed = time.time() - start_time
    print(f"\n✅ All three agents demonstrated successfully!")
    print(f"⏱️  Total time: {elapsed:.2f}s")
    print(f"\n📖 See PREDATOR_SUITE_DOCUMENTATION.md for full documentation")
    print(f"🚀 Run 'python main.py' to start the full trading engine")


if __name__ == "__main__":
    asyncio.run(main())
