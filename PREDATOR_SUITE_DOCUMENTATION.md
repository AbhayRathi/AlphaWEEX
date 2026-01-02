# Aether-Evo "Predator" Suite Documentation

## Overview

The Aether-Evo Predator Suite is a modular trading intelligence system that detects human psychological vulnerabilities and self-evolves based on market outcomes. It consists of three core agents working in harmony:

1. **BehavioralAdversary** - "The Dark Mirror" (Behavioral Analysis)
2. **ReconciliationAuditor** - "The Auditor" (Feedback Loop)
3. **EvolutionaryMutator** - "The DNA Patch" (Self-Correction)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PREDATOR SUITE                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐             │
│  │ BehavioralAdversary│     │ReconciliationAuditor│           │
│  │  (Dark Mirror)     │────▶│    (Auditor)     │             │
│  │                    │     │                  │             │
│  │ - Detects FOMO     │     │ - Tracks results │             │
│  │ - Detects Panic    │     │ - Scores accuracy│             │
│  │ - Liquidity Hunts  │     │ - 1h/4h/12h audit│             │
│  └──────────────────┘     └──────────────────┘             │
│           │                        │                         │
│           │                        │ Failed                  │
│           │                        │ Predictions             │
│           │                        ▼                         │
│           │              ┌──────────────────┐               │
│           │              │EvolutionaryMutator│              │
│           └─────────────▶│   (DNA Patch)    │              │
│                          │                  │               │
│          Predictions     │ - Analyzes fails │               │
│                          │ - Evolves prompt │               │
│                          │ - Version control│               │
│                          └──────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Agent 1: BehavioralAdversary (The Dark Mirror)

### Purpose
Identify where retail traders are making emotional mistakes and predict whale "Liquidity Hunts."

### Key Features

#### Trader Archetypes
- **FOMO Chaser**: Buying extensions after vertical moves (RSI > 70, Price > +3%)
- **Panic Seller**: Capitulating at support levels (RSI < 30, Fear sentiment)
- **Revenge Trader**: Emotional overtrading after losses
- **Liquidity Hunter**: Whale manipulation zones (0.5% below swing lows)

#### Intelligence Modes
1. **API Mode**: DeepSeek-V3 with Chain-of-Thought reasoning
2. **Heuristic Mode**: RSI/Bollinger/Volume fallback (offline operation)
3. **Shadow Mode**: Synthetic $90k BTC data (451 error handling)

#### US-Compatibility
- **451-Error Safety Net**: Auto-activates Shadow Mode on regional blocks
- **Response Time**: < 1 second failover to Shadow Mode
- **Synthetic Data**: Uses $90k BTC candles to keep reasoning active

### Usage Example

```python
from agents.adversary import BehavioralAdversary

# Initialize
adversary = BehavioralAdversary(
    deepseek_api_key="your_key",
    model="deepseek-chat",
    use_shadow_mode=False,  # Auto-activates on 451 errors
    enable_cot=True
)

# Analyze market psychology
market_data = {
    'price': 95000.0,
    'rsi': 78.0,
    'volume': 8000.0,
    'price_change_pct': 5.5,
    'recent_lows': [88000, 87500, 86000]
}

result = adversary.analyze_psychology(
    market_data,
    sentiment="Extreme Greed",
    narrative="ETF Approval News"
)

print(f"Detected: {result['detected_archetype']}")
print(f"Signal: {result['signal']}")
print(f"Confidence: {result['confidence']}")
print(f"Reasoning: {result['reasoning']}")
```

### Output Format (Strict JSON)

```json
{
    "timestamp": "2026-01-02T04:00:00",
    "detected_archetype": "FOMO_CHASER",
    "vulnerability_score": 0.85,
    "predicted_bias": "Bullish Extension",
    "predicted_outcome": "Bull Trap / Reversal",
    "confidence": 0.75,
    "reasoning": "Chain-of-Thought explanation...",
    "signal": "SELL",
    "liquidity_zones": [89550.0, 89100.0, 88200.0],
    "market_regime": "VOLATILE",
    "mode": "API",
    "response_time": 0.423
}
```

## Agent 2: ReconciliationAuditor (The Auditor)

### Purpose
Create a "Memory" for the bot to judge its own intelligence through prediction tracking and validation.

### Key Features

#### Intelligence Ledger (SQLite)
- **Persistent Database**: `data/intelligence_ledger.db`
- **Schema Fields**:
  - `timestamp`: ISO timestamp
  - `predicted_bias`: e.g., "Bullish Extension"
  - `predicted_outcome`: e.g., "Bull Trap / Reversal"
  - `confidence`: 0-1
  - `market_regime`: BULL/BEAR/CHOPPY/VOLATILE
  - `archetype`: FOMO_CHASER, PANIC_SELLER, etc.
  - `signal`: BUY/SELL/HOLD
  - `price_at_prediction`: Float
  - `actual_price_1h/4h/12h`: Float (nullable)
  - `success_score_1h/4h/12h`: -1 to +1 (nullable)
  - `audited`: Boolean

#### Audit Cycles
- **1-hour audit**: Check short-term accuracy
- **4-hour audit**: Medium-term validation
- **12-hour audit**: Long-term assessment

#### Success Scoring Logic
```python
Score Calculation:
- Correct direction prediction: +0.5 to +1.0
- Wrong direction prediction: -0.5 to -1.0
- Weighted by confidence level
- Special bonuses for correctly predicting:
  - Bull/Bear traps: +0.8
  - Mean reversions: +0.7
```

### Usage Example

```python
from agents.reconciliation_loop import IntelligenceLedger, ReconciliationAuditor

# Initialize
ledger = IntelligenceLedger(db_path="data/intelligence_ledger.db")
auditor = ReconciliationAuditor(ledger=ledger)

# Record a prediction
pred_id = ledger.record_prediction(
    predicted_bias="Bullish Extension",
    predicted_outcome="Bull Trap / Reversal",
    confidence=0.8,
    market_regime="BULL",
    archetype="FOMO_CHASER",
    signal="SELL",
    price_at_prediction=95000.0
)

# Run audit cycle (after 1 hour)
auditor.run_audit_cycle(current_price=93000.0)

# Get failed predictions for learning
failed = auditor.get_failed_predictions_for_learning(top_n=5)

# View statistics
stats = ledger.get_statistics()
print(f"Total Predictions: {stats['total_predictions']}")
print(f"Avg Score 1h: {stats['avg_score_1h']:.2f}")
```

### Audit Output

```
🔍 Auditing 1h predictions...
Found 15 predictions to audit for 1h
Prediction #123: Bullish Extension -> Score: -0.64
Prediction #124: Panic Seller -> Score: +0.85

📊 AUDIT STATISTICS
Total Predictions: 150
Audited: 120
Pending Audit: 30
Avg Score 1h: 0.32
Avg Score 4h: 0.28
Avg Score 12h: 0.19
```

## Agent 3: EvolutionaryMutator (The DNA Patch)

### Purpose
Recursive self-improvement through prompt engineering. Analyzes failed predictions and evolves the Adversary's system prompt.

### Key Features

#### Recursive Feedback
- **24-hour cycle**: Collects top 5 failed predictions
- **LLM Analysis**: Uses DeepSeek to analyze why predictions failed
- **Prompt Mutation**: Rewrites Adversary's system prompt to improve

#### Version Control
- **File Format**: `adversary_v[X].txt`
- **Archive System**: Old versions saved to `data/prompts/archive/`
- **Metadata Tracking**: Timestamps and evolution reasons

#### Symmetry Guard (Safety Filter)
Prevents reckless strategies by enforcing:
- ✅ Stop-loss mentions required
- ✅ Risk management language present
- ✅ Chain-of-Thought reasoning maintained
- ❌ Rejects "no stop-loss" suggestions
- ❌ Rejects "all in" strategies
- ❌ Rejects unlimited loss patterns

### Usage Example

```python
from agents.evolutionary_mutator import EvolutionaryMutator

# Initialize
mutator = EvolutionaryMutator(
    prompts_dir="data/prompts",
    deepseek_api_key="your_key",
    model="deepseek-chat",
    evolution_interval_hours=24
)

# Get current prompt
current_prompt = mutator.load_current_prompt()
print(f"Current version: v{mutator.current_version}")

# Evolve based on failures
failed_predictions = [
    {
        'predicted_bias': 'Bullish Extension',
        'predicted_outcome': 'Bull Trap',
        'archetype': 'FOMO_CHASER',
        'signal': 'SELL',
        'confidence': 0.8,
        'price_at_prediction': 95000,
        'actual_price_1h': 96000,
        'avg_score': -0.5
    }
]

new_prompt = mutator.evolve_prompt(failed_predictions, force=True)

if new_prompt:
    print(f"✅ Evolved to v{mutator.current_version}")
else:
    print("❌ Evolution blocked by Symmetry Guard")

# View evolution history
history = mutator.get_evolution_history()
for v in history:
    print(f"v{v['version']}: {v['created']}")
```

### Evolution Output

```
============================================================
PROMPT EVOLUTION CYCLE
============================================================
Analyzing 5 failed predictions...

FAILURE #1:
- Predicted Bias: Bullish Extension
- Predicted Outcome: Bull Trap / Reversal
- Actual: Price continued up
- Score: -0.5

[LLM Analysis...]

✅ Symmetry Guard: Prompt passed safety checks
✅ Successfully evolved prompt to v2

Archived: adversary_v1_20260102_040000.txt
Created: adversary_v2.txt
```

## Integration with Main Orchestrator

The Predator Suite is fully integrated into `main.py` via the `predator_suite_loop()`:

```python
async def predator_suite_loop(self):
    """
    Orchestrates the three Predator Suite agents:
    1. Behavioral analysis every 15 minutes
    2. Audits at 1h, 4h, 12h intervals
    3. Evolution every 24 hours
    """
    while self.running:
        # 1. Run behavioral analysis
        market_data = await fetch_market_data()
        analysis = self.behavioral_adversary.analyze_psychology(market_data)
        
        # Record prediction
        self.intelligence_ledger.record_prediction(...)
        
        # 2. Run audits (time-based)
        if time_for_1h_audit:
            self.reconciliation_auditor._audit_timeframe("1h", 1, current_price)
        
        # 3. Evolve prompt (24h cycle)
        if time_for_evolution:
            failed = self.reconciliation_auditor.get_failed_predictions_for_learning(5)
            self.evolutionary_mutator.evolve_prompt(failed)
        
        await asyncio.sleep(900)  # 15 minutes
```

## Configuration

Add to `.env`:

```bash
# DeepSeek Configuration (required for Predator Suite)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat

# Optional: Override defaults
PREDATOR_EVOLUTION_INTERVAL=24  # hours
PREDATOR_AUDIT_1H=60           # minutes
PREDATOR_AUDIT_4H=240          # minutes
PREDATOR_AUDIT_12H=720         # minutes
```

## Validation Tests

All three agents include comprehensive tests:

### Flash Crash Test
```bash
python agents/adversary.py
# ✅ Detects Human Panic, recommends Contrarian Entry
```

### 451 Error Test
```bash
python agents/adversary.py
# ✅ Shadow Mock Mode activated within <1 second
```

### Audit Test (False Positive Detection)
```bash
python agents/reconciliation_loop.py
# ✅ False Positive detected, score: -0.64
```

### Full Integration Test
```bash
python -m pytest tests/test_predator_suite.py -v
# ✅ 18 tests passed
```

## Performance Metrics

- **Response Time**: < 1s for heuristic mode, < 5s for API mode
- **Shadow Mode Activation**: < 1s on 451 errors
- **Memory Usage**: ~50MB for SQLite ledger (1000 predictions)
- **Evolution Cycle**: ~30s with API (depends on LLM response)

## Security Features

1. **Credential Safety**: All keys loaded from environment
2. **Metadata Stripping**: Sensitive server info removed before API calls
3. **Symmetry Guard**: Prevents reckless strategy mutations
4. **Database Isolation**: SQLite with proper permissions
5. **Version Control**: All prompt changes tracked and reversible

## Future Enhancements

- [ ] Multi-timeframe analysis (1m, 5m, 15m, 1h)
- [ ] Sentiment API integration (Fear & Greed Index)
- [ ] Whale alert service integration
- [ ] Advanced archetype detection (Range Trader, Breakout Chaser)
- [ ] Multi-asset correlation analysis
- [ ] Real-time dashboard visualization

## Troubleshooting

### Issue: 451 Error Not Triggering Shadow Mode
**Solution**: Check logs for "Activating Shadow Mock Mode" message. Ensure `use_shadow_mode` auto-activation is working.

### Issue: Evolution Not Running
**Solution**: Check that 24 hours have passed since last evolution. Use `force=True` for testing.

### Issue: Low Prediction Accuracy
**Solution**: Review failed predictions in ledger. Evolution cycle will automatically improve thresholds.

### Issue: Database Locked
**Solution**: Ensure only one process accesses the SQLite database at a time. Use async operations properly.

## Support

For issues or questions:
- Review test files: `tests/test_predator_suite.py`
- Check individual agent tests: Run `python agents/adversary.py` etc.
- Consult logs: `data/intelligence_ledger.db` for audit history
- Evolution history: `data/prompts/` for prompt versions

## License

MIT License - See LICENSE file for details

---

**Built for the WEEX AI Trading Hackathon**  
**Aether-Evo: Self-Evolving Trading Intelligence**
