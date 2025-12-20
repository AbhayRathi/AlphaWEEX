"""
Stochastic Alpha Explorer Agent
Triggers every 6 hours with High Temperature (1.3) via DeepSeek-V3
Generates novel trading hypotheses based on failed strategies
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StochasticAlphaExplorer:
    """
    Stochastic Alpha Explorer Agent
    
    Features:
    - Triggers every 6 hours
    - Uses DeepSeek-V3 with high temperature (1.3) for creative exploration
    - Analyzes failed strategies from evolution history
    - Generates novel trading hypotheses
    """
    
    def __init__(
        self,
        deepseek_config,
        evolution_memory,
        interval_hours: int = 6,
        temperature: float = 1.3
    ):
        """
        Initialize Stochastic Alpha Explorer
        
        Args:
            deepseek_config: DeepSeek API configuration
            evolution_memory: Evolution memory for accessing failed strategies
            interval_hours: Exploration interval in hours (default: 6)
            temperature: Temperature for creative exploration (default: 1.3)
        """
        self.deepseek_config = deepseek_config
        self.evolution_memory = evolution_memory
        self.interval_hours = interval_hours
        self.temperature = temperature
        self.running = False
        self.latest_hypothesis: Optional[Dict[str, Any]] = None
        self.hypothesis_history: List[Dict[str, Any]] = []
        
    def _get_failed_strategies(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get the last N failed strategies from evolution history
        
        Args:
            count: Number of failed strategies to retrieve
            
        Returns:
            List of failed strategy records
        """
        blacklisted = self.evolution_memory.data.get("blacklisted_parameters", [])
        # Sort by timestamp, most recent first
        sorted_blacklisted = sorted(
            blacklisted,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        return sorted_blacklisted[:count]
    
    def _format_failed_strategies_prompt(self, failed_strategies: List[Dict[str, Any]]) -> str:
        """
        Format failed strategies into a prompt for DeepSeek-V3
        
        Args:
            failed_strategies: List of failed strategy records
            
        Returns:
            Formatted prompt string
        """
        if not failed_strategies:
            return "**No failed strategies recorded yet.** This is a clean slate for exploration."
        
        prompt = "## Failed Strategies Analysis\n\n"
        prompt += f"The following {len(failed_strategies)} strategies were tried and failed:\n\n"
        
        for i, strategy in enumerate(failed_strategies, 1):
            prompt += f"### Strategy {i}\n"
            prompt += f"- **Timestamp**: {strategy.get('timestamp', 'Unknown')}\n"
            prompt += f"- **Reason**: {strategy.get('reason', 'No reason provided')}\n"
            prompt += f"- **PnL**: {strategy.get('pnl', 0):.2f}\n"
            prompt += f"- **Parameters**: {json.dumps(strategy.get('parameters', {}), indent=2)}\n"
            prompt += "\n"
        
        return prompt
    
    async def _call_deepseek_v3(
        self,
        prompt: str,
        regime: str
    ) -> Dict[str, Any]:
        """
        Call DeepSeek-V3 API with high temperature for creative exploration
        
        Args:
            prompt: The exploration prompt
            regime: Current market regime
            
        Returns:
            Hypothesis response from DeepSeek-V3
            
        Note: This is a simulated implementation. In production, integrate with
        actual DeepSeek API using aiohttp or official SDK.
        """
        # Simulated response - in production, make actual API call
        logger.info(f"Calling DeepSeek-V3 with temperature {self.temperature}...")
        logger.info(f"API Key configured: {bool(self.deepseek_config.api_key)}")
        
        # Simulate API call delay
        await asyncio.sleep(1)
        
        # Generate creative hypothesis based on regime
        hypothesis_examples = {
            "TRENDING_UP": "Trading the gap between Spot and Futures funding rates on WEEX during strong uptrends",
            "TRENDING_DOWN": "Shorting high RSI divergences during downtrends with volume confirmation",
            "RANGE_VOLATILE": "Mean reversion scalping using Bollinger Band squeeze and expansion patterns",
            "RANGE_QUIET": "Breakout anticipation using volume accumulation and order flow imbalance",
            "UNKNOWN": "Multi-timeframe confluence strategy combining 15m, 1h, and 4h trend alignment"
        }
        
        hypothesis_text = hypothesis_examples.get(
            regime,
            "Adaptive momentum strategy using regime-specific parameter optimization"
        )
        
        return {
            "hypothesis": hypothesis_text,
            "confidence": 0.65,
            "reasoning": f"Generated novel strategy idea for {regime} market regime using stochastic exploration",
            "suggested_indicators": [
                "Funding rate differential",
                "Volume profile",
                "RSI divergence",
                "Order flow imbalance"
            ],
            "implementation_hints": [
                "Monitor funding rate every 8 hours",
                "Compare spot price vs perpetual futures",
                "Look for funding rate > 0.1% as signal",
                "Use 4-hour timeframe for trend confirmation"
            ]
        }
    
    async def explore(self, current_regime: str) -> Dict[str, Any]:
        """
        Perform stochastic exploration to generate a new alpha hypothesis
        
        Args:
            current_regime: Current market regime from regime detector
            
        Returns:
            Hypothesis dictionary with exploration results
        """
        logger.info("🔍 Stochastic Alpha Explorer: Starting exploration...")
        
        # Get failed strategies
        failed_strategies = self._get_failed_strategies(count=5)
        logger.info(f"Analyzing {len(failed_strategies)} failed strategies")
        
        # Build exploration prompt
        failed_prompt = self._format_failed_strategies_prompt(failed_strategies)
        
        exploration_prompt = f"""
# Stochastic Alpha Explorer - Creative Strategy Generation

## Mission
Generate a NOVEL trading signal hypothesis that has NOT been tried before.
Use high creativity and explore unconventional ideas.

## Current Market Context
- **Regime**: {current_regime}
- **Temperature**: {self.temperature} (High creativity mode)

{failed_prompt}

## Task
Based on the failed strategies above and current market regime, propose a completely 
NEW hypothesis for a trading signal. Think outside the box!

Examples of creative hypotheses:
1. Trading the gap between Spot and Futures funding rates
2. Exploiting order book imbalance in the top 5 levels
3. Following smart money flows via large transaction tracking
4. Cross-exchange arbitrage opportunities
5. Volatility regime switching strategies

**Your Hypothesis:**
"""
        
        # Call DeepSeek-V3 with high temperature
        response = await self._call_deepseek_v3(exploration_prompt, current_regime)
        
        # Create hypothesis record
        hypothesis = {
            "timestamp": datetime.now().isoformat(),
            "regime": current_regime,
            "hypothesis": response["hypothesis"],
            "confidence": response["confidence"],
            "reasoning": response["reasoning"],
            "suggested_indicators": response.get("suggested_indicators", []),
            "implementation_hints": response.get("implementation_hints", []),
            "temperature": self.temperature,
            "failed_strategies_analyzed": len(failed_strategies)
        }
        
        # Store hypothesis
        self.latest_hypothesis = hypothesis
        self.hypothesis_history.append(hypothesis)
        
        logger.info(f"✨ New Hypothesis Generated: {hypothesis['hypothesis']}")
        logger.info(f"   Confidence: {hypothesis['confidence']:.2%}")
        
        return hypothesis
    
    async def run_loop(self, regime_detector_callback):
        """
        Run the exploration loop every 6 hours
        
        Args:
            regime_detector_callback: Async function that returns current market regime
        """
        logger.info(f"🚀 Stochastic Alpha Explorer started (interval: {self.interval_hours}h)")
        self.running = True
        
        while self.running:
            try:
                # Get current market regime
                current_regime = await regime_detector_callback()
                
                # Perform exploration
                hypothesis = await self.explore(current_regime)
                
                # Log hypothesis
                logger.info("=" * 60)
                logger.info("🔬 NEW ALPHA HYPOTHESIS")
                logger.info("=" * 60)
                logger.info(f"Regime: {hypothesis['regime']}")
                logger.info(f"Hypothesis: {hypothesis['hypothesis']}")
                logger.info(f"Confidence: {hypothesis['confidence']:.2%}")
                logger.info(f"Indicators: {', '.join(hypothesis['suggested_indicators'])}")
                logger.info("=" * 60)
                
                # Wait for next exploration cycle (6 hours)
                wait_seconds = self.interval_hours * 3600
                logger.info(f"⏰ Next exploration in {self.interval_hours} hours...")
                await asyncio.sleep(wait_seconds)
                
            except Exception as e:
                logger.error(f"Error in exploration loop: {str(e)}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    def stop(self):
        """Stop the exploration loop"""
        logger.info("Stopping Stochastic Alpha Explorer...")
        self.running = False
    
    def get_latest_hypothesis(self) -> Optional[Dict[str, Any]]:
        """Get the latest generated hypothesis"""
        return self.latest_hypothesis
    
    def get_hypothesis_history(self) -> List[Dict[str, Any]]:
        """Get all generated hypotheses"""
        return self.hypothesis_history
