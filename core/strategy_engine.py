"""
LLM-Based Strategy Engine for Autonomous Trading Decisions

Replaces traditional RSI/SMA rules with AI reasoning using OpenAI or Anthropic.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional imports for LLM providers
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic not available. Install with: pip install anthropic")


class StrategyEngine:
    """
    LLM-powered trading strategy engine
    
    Features:
    - OpenAI GPT-4 integration
    - Anthropic Claude integration
    - Context-aware prompting with market data
    - Trade history memory integration
    - JSON response parsing
    """
    
    def __init__(self, provider: Literal["openai", "anthropic"] = "openai",
                 api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Strategy Engine
        
        Args:
            provider: LLM provider ("openai" or "anthropic")
            api_key: API key for the LLM provider
            model: Model name (optional, uses defaults)
        """
        self.provider = provider
        self.api_key = api_key
        
        # Set default models
        if model:
            self.model = model
        elif provider == "openai":
            self.model = "gpt-4o-mini"  # Cost-effective and fast
        elif provider == "anthropic":
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.model = None
        
        # Validate provider availability
        if provider == "openai" and not OPENAI_AVAILABLE:
            raise ImportError("OpenAI not installed. Install with: pip install openai")
        if provider == "anthropic" and not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic not installed. Install with: pip install anthropic")
        
        if not api_key:
            raise ValueError(f"API key required for {provider}")
        
        # Initialize client
        if provider == "openai":
            self.client = openai.OpenAI(api_key=api_key)
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)
        
        logger.info(f"✅ StrategyEngine initialized: {provider} ({self.model})")
    
    def _format_candles_data(self, klines: List[List], limit: int = 100) -> str:
        """
        Format K-lines data for LLM prompt
        
        Args:
            klines: K-lines data [[timestamp, open, high, low, close, volume], ...]
            limit: Maximum number of candles to include
            
        Returns:
            Formatted string with recent candles
        """
        if not klines:
            return "No market data available"
        
        # Take last N candles
        recent_klines = klines[-limit:] if len(klines) > limit else klines
        
        # Calculate some basic stats
        closes = [float(candle[4]) for candle in recent_klines]
        volumes = [float(candle[5]) if len(candle) > 5 else 0.0 for candle in recent_klines]
        
        current_price = closes[-1]
        price_change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100 if closes[0] != 0 else 0.0
        avg_volume = sum(volumes) / len(volumes) if volumes else 0.0
        
        # Format summary
        summary = f"""Market Data Summary:
- Current Price: ${current_price:.2f}
- Price Change (period): {price_change_pct:+.2f}%
- Average Volume: {avg_volume:.2f}
- Data Points: {len(recent_klines)} candles
- Price Range: ${min(closes):.2f} - ${max(closes):.2f}

Recent Price Action (last 10 candles):
"""
        
        # Add last 10 candles for detailed view
        for i, candle in enumerate(recent_klines[-10:], 1):
            timestamp = candle[0]
            open_price = float(candle[1])
            high = float(candle[2])
            low = float(candle[3])
            close = float(candle[4])
            volume = float(candle[5]) if len(candle) > 5 else 0.0
            
            summary += f"{i}. O: ${open_price:.2f}, H: ${high:.2f}, L: ${low:.2f}, C: ${close:.2f}, Vol: {volume:.2f}\n"
        
        return summary
    
    def _format_trade_history(self, performance: Dict[str, Any]) -> str:
        """
        Format trade history for LLM prompt
        
        Args:
            performance: Performance metrics from DatabaseManager
            
        Returns:
            Formatted string with trade history
        """
        if not performance or performance.get("total_trades", 0) == 0:
            return "No trade history available (this is our first trade)"
        
        history = f"""Trading Performance History:
- Total Trades: {performance['total_trades']}
- Win Rate: {performance['win_rate'] * 100:.1f}%
- Average P&L: {performance['avg_profit']:+.2f}%
- Total P&L: {performance['total_pnl']:+.2f}%
- Best Trade: {performance.get('best_trade', 0.0):+.2f}%
- Worst Trade: {performance.get('worst_trade', 0.0):+.2f}%

Recent Trades:
"""
        
        recent_trades = performance.get("recent_trades", [])
        for i, trade in enumerate(recent_trades[:5], 1):
            outcome = trade.get('outcome', 0.0)
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            history += f"{i}. {side} {symbol}: {outcome:+.2f}% P&L\n"
        
        return history
    
    def _build_prompt(self, symbol: str, klines: List[List], 
                     performance: Dict[str, Any], balance: float = 1000.0,
                     leverage: int = 20) -> str:
        """
        Build the complete prompt for LLM
        
        Args:
            symbol: Trading symbol
            klines: Market K-lines data
            performance: Recent performance metrics
            balance: Current balance in USDT
            leverage: Trading leverage
            
        Returns:
            Complete prompt string
        """
        candles_data = self._format_candles_data(klines)
        trade_history = self._format_trade_history(performance)
        
        prompt = f"""You are an expert cryptocurrency trader managing a futures trading account with {leverage}x leverage.

CURRENT SITUATION:
- Symbol: {symbol}
- Balance: ${balance:.2f} USDT
- Leverage: {leverage}x
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{candles_data}

{trade_history}

TASK:
Based on the market data and our trading history, make a decision: should we BUY, SELL, or HOLD?

IMPORTANT RULES:
1. We use {leverage}x leverage, so risk is amplified
2. Consider market momentum, volume, and price action
3. Use our trading history to learn from past successes and failures
4. Protect our ${balance:.2f} USDT balance
5. Be conservative - it's better to HOLD than to make a bad trade

RESPONSE FORMAT:
You must respond with valid JSON in this exact format:
{{
    "action": "BUY" or "SELL" or "HOLD",
    "confidence": 0.0 to 1.0,
    "reasoning": "Your detailed explanation of why you chose this action. Explain what you see in the market data, how our past performance influences this decision, and why this is the best move to protect and grow our balance."
}}

Your reasoning should be clear and explain:
- What patterns you see in the price action
- How volume and momentum support your decision
- What you learned from our recent trade history
- Why this protects or grows our {balance} USDT balance

Respond only with the JSON object, no additional text."""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI API
        
        Args:
            prompt: Prompt text
            
        Returns:
            Parsed response dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert cryptocurrency trader. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """
        Call Anthropic API
        
        Args:
            prompt: Prompt text
            
        Returns:
            Parsed response dictionary
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Try to extract JSON from response
            # Anthropic might wrap JSON in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    def get_decision(self, symbol: str, klines: List[List], 
                    performance: Dict[str, Any], balance: float = 1000.0,
                    leverage: int = 20) -> Dict[str, Any]:
        """
        Get trading decision from LLM
        
        Args:
            symbol: Trading symbol
            klines: Market K-lines data
            performance: Recent performance metrics from database
            balance: Current balance in USDT
            leverage: Trading leverage
            
        Returns:
            Dictionary with:
            - action: "BUY", "SELL", or "HOLD"
            - confidence: 0.0 to 1.0
            - reasoning: Detailed explanation from LLM
        """
        try:
            # Build prompt
            prompt = self._build_prompt(symbol, klines, performance, balance, leverage)
            
            # Call LLM based on provider
            if self.provider == "openai":
                response = self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
            
            # Validate response
            action = response.get("action", "HOLD").upper()
            if action not in ["BUY", "SELL", "HOLD"]:
                logger.warning(f"Invalid action from LLM: {action}, defaulting to HOLD")
                action = "HOLD"
            
            confidence = float(response.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            reasoning = response.get("reasoning", "No reasoning provided")
            
            logger.info(f"🤖 LLM Decision: {action} (confidence: {confidence:.2%})")
            logger.info(f"💭 Reasoning: {reasoning[:100]}...")
            
            return {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"Failed to get LLM decision: {str(e)}")
            # Fallback to conservative HOLD decision
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": f"Error getting LLM decision: {str(e)}. Defaulting to HOLD for safety.",
                "error": str(e)
            }
