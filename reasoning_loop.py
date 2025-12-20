"""
Reasoning Loop - R1 analyzes OHLCV data every 15 minutes
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from data.regime import ohlcv_list_to_dataframe, get_regime_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReasoningLoop:
    """
    15-minute Reasoning Loop using DeepSeek R1/V3
    Analyzes OHLCV data and generates trading insights
    """
    
    def __init__(self, discovery_agent, deepseek_config, interval_minutes: int = 15, evolution_memory=None):
        """Initialize Reasoning Loop"""
        self.discovery_agent = discovery_agent
        self.deepseek_config = deepseek_config
        self.interval_minutes = interval_minutes
        self.running = False
        self.latest_analysis: Optional[Dict[str, Any]] = None
        self.evolution_memory = evolution_memory
        
    def _format_markdown_snapshot(self, ohlcv_data: List[List], regime_metrics: Dict[str, Any]) -> str:
        """
        Format OHLCV data and regime into a Markdown table snapshot
        
        Args:
            ohlcv_data: List of [timestamp, open, high, low, close, volume]
            regime_metrics: Regime detection metrics
            
        Returns:
            Markdown formatted table string
        """
        if len(ohlcv_data) < 1:
            return "**No data available**"
        
        # Get latest candle
        latest = ohlcv_data[-1]
        timestamp, open_price, high, low, close, volume = latest
        
        # Format timestamp
        dt = datetime.fromtimestamp(timestamp / 1000)
        
        # Get previous close for change calculation
        prev_close = ohlcv_data[-2][4] if len(ohlcv_data) > 1 else close
        change = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
        
        # Build markdown table
        markdown = f"""
## Market Snapshot - {dt.strftime('%Y-%m-%d %H:%M:%S')}

### Price Action
| Metric | Value | Change |
|--------|-------|--------|
| **Open** | ${open_price:.2f} | - |
| **High** | ${high:.2f} | - |
| **Low** | ${low:.2f} | - |
| **Close** | ${close:.2f} | {change:+.2f}% |
| **Volume** | {volume:.2f} | - |

### Technical Indicators
| Indicator | Value | Interpretation |
|-----------|-------|----------------|
| **RSI** | {regime_metrics.get('rsi', 50):.2f} | {'Overbought' if regime_metrics.get('rsi', 50) > 70 else 'Oversold' if regime_metrics.get('rsi', 50) < 30 else 'Neutral'} |
| **ATR** | {regime_metrics.get('atr', 0):.4f} | Volatility measure |
| **ADX** | {regime_metrics.get('adx', 0):.2f} | {'Strong trend' if regime_metrics.get('adx', 0) > 25 else 'Weak/No trend'} |
| **+DI** | {regime_metrics.get('plus_di', 0):.2f} | Positive directional |
| **-DI** | {regime_metrics.get('minus_di', 0):.2f} | Negative directional |

### Market Regime
**Current Regime:** `{regime_metrics.get('regime', 'UNKNOWN')}`

---
"""
        return markdown
        
    async def analyze_ohlcv(self, ohlcv_data: List[List], symbol: str) -> Dict[str, Any]:
        """
        Analyze OHLCV data using DeepSeek R1 reasoning with regime awareness
        
        Args:
            ohlcv_data: List of [timestamp, open, high, low, close, volume]
            symbol: Trading symbol
            
        Returns:
            Analysis results with trading signals and reasoning
        """
        logger.info(f"Analyzing OHLCV data for {symbol}...")
        
        # Extract recent data
        if len(ohlcv_data) < 2:
            return {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'signal': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'Insufficient data for analysis',
                'evolution_suggestion': None,
                'regime': 'UNKNOWN'
            }
        
        # Convert to DataFrame and detect regime
        ohlcv_df = ohlcv_list_to_dataframe(ohlcv_data)
        regime_metrics = get_regime_metrics(ohlcv_df)
        regime = regime_metrics['regime']
        
        # Format markdown snapshot
        markdown_snapshot = self._format_markdown_snapshot(ohlcv_data, regime_metrics)
        
        # Calculate basic indicators
        recent_candles = ohlcv_data[-20:] if len(ohlcv_data) >= 20 else ohlcv_data
        closes = [candle[4] for candle in recent_candles]
        volumes = [candle[5] for candle in recent_candles]
        
        # Simple trend analysis
        current_price = closes[-1]
        prev_price = closes[-2] if len(closes) > 1 else current_price
        price_change = (current_price - prev_price) / prev_price if prev_price > 0 else 0
        
        # Calculate simple moving averages
        sma_short = sum(closes[-5:]) / min(5, len(closes)) if closes else 0
        sma_long = sum(closes) / len(closes) if closes else 0
        
        # Volume analysis
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        current_volume = volumes[-1]
        volume_spike = current_volume > avg_volume * 1.5
        
        # Regime-aware reasoning (simulated - in production, call DeepSeek R1 API)
        signal = 'HOLD'
        confidence = 0.5
        reasoning = []
        evolution_suggestion = None
        
        # Generate prompt for DeepSeek-R1
        r1_prompt = f"""{markdown_snapshot}

**Performance History:**
{self._get_performance_summary()}

**Question for DeepSeek-R1:**
Based on this regime ({regime}) and performance history, should we mutate active_logic.py?
Consider:
1. Is the current strategy well-suited for this market regime?
2. Have recent evolutions been successful or failed?
3. Are there blacklisted parameters we should avoid?
4. What specific improvements would help in this regime?
"""
        
        # Regime-aware signal generation
        if regime == 'TRENDING_UP':
            if current_price > sma_long and current_price > sma_short:
                if price_change > 0.01 and volume_spike:
                    signal = 'BUY'
                    confidence = 0.80
                    reasoning.append("Strong uptrend confirmed by regime detection with volume")
                elif price_change > 0.005:
                    signal = 'BUY'
                    confidence = 0.70
                    reasoning.append("Trending up regime - moderate buy signal")
        elif regime == 'TRENDING_DOWN':
            if current_price < sma_long and current_price < sma_short:
                if price_change < -0.01 and volume_spike:
                    signal = 'SELL'
                    confidence = 0.80
                    reasoning.append("Strong downtrend confirmed by regime detection with volume")
                elif price_change < -0.005:
                    signal = 'SELL'
                    confidence = 0.70
                    reasoning.append("Trending down regime - moderate sell signal")
        elif regime == 'RANGE_VOLATILE':
            # In volatile range, be cautious
            reasoning.append("Range-volatile regime - waiting for clearer signals")
            confidence = 0.40
        elif regime == 'RANGE_QUIET':
            # In quiet range, look for breakout opportunities
            reasoning.append("Range-quiet regime - watching for breakout")
            confidence = 0.45
        else:
            reasoning.append("Mixed signals, maintaining current position")
        
        # Suggest evolution if confidence is low or regime suggests need for adaptation
        if confidence < 0.6:
            evolution_suggestion = {
                # Note: .2% format multiplies by 100 and adds % (e.g., 0.6 -> 60.00%)
                'reason': f'Low confidence ({confidence:.2%}) in {regime} regime',
                'suggestion': f'Adapt strategy for {regime} market conditions. Consider regime-specific indicators and rules.'
            }
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'reasoning': ' | '.join(reasoning),
            'regime': regime,
            'regime_metrics': regime_metrics,
            'markdown_snapshot': markdown_snapshot,
            'r1_prompt': r1_prompt,
            'metrics': {
                'current_price': current_price,
                'price_change': price_change,
                'sma_short': sma_short,
                'sma_long': sma_long,
                'volume_spike': volume_spike
            },
            'evolution_suggestion': evolution_suggestion
        }
        
        logger.info(f"Analysis complete: {signal} with {confidence:.2%} confidence in {regime} regime")
        return analysis
    
    
    def _get_performance_summary(self) -> str:
        """
        Get performance history summary for R1 reasoning
        
        Returns:
            Formatted string with recent performance and blacklisted parameters
        """
        if not self.evolution_memory:
            return "No performance history available."
        
        stats = self.evolution_memory.get_statistics()
        recent = self.evolution_memory.get_recent_evolutions(3)
        
        summary = f"""
- Total evolutions: {stats['total_evolutions']}
- Success rate: {stats['success_rate']:.1f}%
- Blacklisted parameter sets: {stats['blacklisted_parameters']}
- Pending evaluations: {stats['pending_evaluations']}
"""
        
        if recent:
            summary += "\n**Recent Evolutions:**\n"
            for i, evo in enumerate(recent, 1):
                pnl = evo.get('final_pnl', evo.get('current_pnl', 'pending'))
                summary += f"{i}. {evo.get('reason', 'Unknown')} - PnL: {pnl}\n"
        
        return summary
    
    async def run_loop(self, symbol: str):
        """Run the reasoning loop continuously"""
        logger.info(f"Starting reasoning loop with {self.interval_minutes}m interval...")
        self.running = True
        
        while self.running:
            try:
                # Fetch OHLCV data
                ohlcv_data = await self.discovery_agent.fetch_ohlcv(
                    symbol,
                    timeframe='15m',
                    limit=100
                )
                
                # Analyze data
                analysis = await self.analyze_ohlcv(ohlcv_data, symbol)
                self.latest_analysis = analysis
                
                # Log analysis
                logger.info(f"Signal: {analysis['signal']}, Confidence: {analysis['confidence']:.2%}")
                logger.info(f"Reasoning: {analysis['reasoning']}")
                
                # Wait for next interval
                await asyncio.sleep(self.interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in reasoning loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop(self):
        """Stop the reasoning loop"""
        logger.info("Stopping reasoning loop...")
        self.running = False
    
    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the latest analysis results"""
        return self.latest_analysis
