"""
Reasoning Loop - R1 analyzes OHLCV data every 15 minutes
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReasoningLoop:
    """
    15-minute Reasoning Loop using DeepSeek R1/V3
    Analyzes OHLCV data and generates trading insights
    """
    
    def __init__(self, discovery_agent, deepseek_config, interval_minutes: int = 15):
        """Initialize Reasoning Loop"""
        self.discovery_agent = discovery_agent
        self.deepseek_config = deepseek_config
        self.interval_minutes = interval_minutes
        self.running = False
        self.latest_analysis: Optional[Dict[str, Any]] = None
        
    async def analyze_ohlcv(self, ohlcv_data: List[List], symbol: str) -> Dict[str, Any]:
        """
        Analyze OHLCV data using DeepSeek R1 reasoning
        
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
                'evolution_suggestion': None
            }
        
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
        
        # R1 Reasoning simulation (in production, call DeepSeek API)
        signal = 'HOLD'
        confidence = 0.5
        reasoning = []
        evolution_suggestion = None
        
        # Generate trading signal based on analysis
        if current_price > sma_long and current_price > sma_short:
            if price_change > 0.01 and volume_spike:
                signal = 'BUY'
                confidence = 0.75
                reasoning.append("Strong uptrend with volume confirmation")
            elif price_change > 0.005:
                signal = 'BUY'
                confidence = 0.65
                reasoning.append("Moderate uptrend detected")
        elif current_price < sma_long and current_price < sma_short:
            if price_change < -0.01 and volume_spike:
                signal = 'SELL'
                confidence = 0.75
                reasoning.append("Strong downtrend with volume confirmation")
            elif price_change < -0.005:
                signal = 'SELL'
                confidence = 0.65
                reasoning.append("Moderate downtrend detected")
        else:
            reasoning.append("Mixed signals, maintaining current position")
        
        # Suggest evolution if confidence is low
        if confidence < 0.6:
            evolution_suggestion = {
                'reason': 'Low confidence in current logic',
                'suggestion': 'Consider adding RSI and MACD indicators for better signal quality'
            }
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'reasoning': ' | '.join(reasoning),
            'metrics': {
                'current_price': current_price,
                'price_change': price_change,
                'sma_short': sma_short,
                'sma_long': sma_long,
                'volume_spike': volume_spike
            },
            'evolution_suggestion': evolution_suggestion
        }
        
        logger.info(f"Analysis complete: {signal} with {confidence:.2%} confidence")
        return analysis
    
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
