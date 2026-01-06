"""
LLM-Based Strategy Engine for Autonomous AI Trading
Replaces indicator-based rules with LLM reasoning
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMStrategy:
    """
    LLM-Based Trading Strategy
    
    Features:
    - Analyzes 50 candles + past trade performance
    - Generates BUY/SELL/HOLD decisions with reasoning
    - Confidence-based execution (>80 threshold)
    - Robust JSON parsing with error handling
    """
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """
        Initialize LLM Strategy
        
        Args:
            model: LLM model to use (default: gpt-4o-mini)
            api_key: OpenAI API key (reads from env if not provided)
        """
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("⚠️ OPENAI_API_KEY not set - LLM strategy will not work")
        
        self.confidence_threshold = 80  # Only execute if confidence > 80
        
        logger.info(f"✅ LLM Strategy initialized (model: {model})")
    
    def _format_candles(self, klines: List[List]) -> str:
        """
        Format candles data for LLM prompt
        
        Args:
            klines: List of candles [[timestamp, open, high, low, close, volume], ...]
            
        Returns:
            Formatted string of candle data
        """
        if not klines:
            return "No candle data available"
        
        # Take last 50 candles
        recent_candles = klines[-50:] if len(klines) > 50 else klines
        
        lines = ["Recent Price Data (Last 50 Candles):"]
        lines.append("Timestamp | Open | High | Low | Close | Volume")
        lines.append("-" * 70)
        
        for candle in recent_candles:
            try:
                timestamp = datetime.fromtimestamp(int(candle[0]) / 1000).strftime('%Y-%m-%d %H:%M')
                open_price = float(candle[1])
                high = float(candle[2])
                low = float(candle[3])
                close = float(candle[4])
                volume = float(candle[5]) if len(candle) > 5 else 0.0
                
                lines.append(f"{timestamp} | {open_price:.2f} | {high:.2f} | {low:.2f} | {close:.2f} | {volume:.2f}")
            except (IndexError, ValueError) as e:
                logger.warning(f"Skipping malformed candle: {e}")
                continue
        
        return "\n".join(lines)
    
    def _format_past_trades(self, past_trades: List[Dict[str, Any]]) -> str:
        """
        Format past trade performance for LLM prompt
        
        Args:
            past_trades: List of recent trades from database
            
        Returns:
            Formatted string of trade history
        """
        if not past_trades:
            return "No past trade history available"
        
        lines = ["Past Trade Performance (Last 5 Trades):"]
        lines.append("Symbol | Side | Price | PnL | Confidence | Reasoning")
        lines.append("-" * 80)
        
        for trade in past_trades:
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            price = trade.get('price', 0.0)
            pnl = trade.get('pnl', 0.0)
            confidence = trade.get('confidence', 0.0)
            reasoning = trade.get('reasoning', 'N/A')[:30]  # Truncate long reasoning
            
            lines.append(f"{symbol} | {side} | ${price:.2f} | {pnl:+.2f}% | {confidence:.0f}% | {reasoning}")
        
        return "\n".join(lines)
    
    def _build_prompt(self, symbol: str, klines: List[List], 
                     past_trades: List[Dict[str, Any]]) -> str:
        """
        Build LLM prompt for trading decision
        
        Args:
            symbol: Trading symbol
            klines: Candle data
            past_trades: Recent trade history
            
        Returns:
            Complete prompt string
        """
        candles_text = self._format_candles(klines)
        trades_text = self._format_past_trades(past_trades)
        
        prompt = f"""You are an expert cryptocurrency trader analyzing {symbol}.

{candles_text}

{trades_text}

Based on the above data, provide a trading decision.

**Instructions:**
1. Analyze the price trends, patterns, and past performance
2. Consider if past trades were successful or not
3. Decide: BUY (open long), SELL (close position if held), or HOLD (no action)
4. Provide confidence level (0-100)
5. Give a brief reason (max 20 words)

**Response Format (JSON only):**
{{
  "action": "BUY" | "SELL" | "HOLD",
  "confidence": 85,
  "reason": "Strong upward momentum with RSI recovery from oversold"
}}

Respond ONLY with valid JSON, no other text."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Call LLM API with prompt
        
        Args:
            prompt: The prompt to send to LLM
            
        Returns:
            Parsed JSON response or None if failed
        """
        if not self.api_key:
            logger.error("❌ Cannot call LLM: API key not set")
            return None
        
        try:
            # Try to import openai
            try:
                import openai
            except ImportError:
                logger.error("❌ openai package not installed. Install with: pip install openai")
                return None
            
            # Create OpenAI client
            client = openai.OpenAI(api_key=self.api_key)
            
            # Call API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert cryptocurrency trading AI. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            # Extract response
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    # Extract JSON from code block
                    lines = content.split("\n")
                    json_lines = []
                    in_block = False
                    for line in lines:
                        if line.strip().startswith("```"):
                            in_block = not in_block
                            continue
                        if in_block or not line.strip().startswith("```"):
                            json_lines.append(line)
                    content = "\n".join(json_lines).strip()
                
                result = json.loads(content)
                logger.info(f"✅ LLM response: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse LLM JSON response: {e}")
                logger.error(f"Raw response: {content}")
                return None
                
        except Exception as e:
            logger.error(f"❌ LLM API call failed: {str(e)}")
            return None
    
    def generate_signal(self, symbol: str, klines: List[List], 
                       past_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate trading signal using LLM
        
        Args:
            symbol: Trading symbol
            klines: Candle data
            past_trades: Recent trade history from database
            
        Returns:
            Signal dictionary with action, confidence, and reason
        """
        # Validate inputs
        if not klines or len(klines) == 0:
            logger.warning(f"⚠️ No candle data for {symbol}")
            return {
                "action": "HOLD",
                "confidence": 0,
                "reason": "No candle data available",
                "executable": False
            }
        
        # Build prompt
        prompt = self._build_prompt(symbol, klines, past_trades)
        
        # Call LLM
        llm_response = self._call_llm(prompt)
        
        if not llm_response:
            logger.warning(f"⚠️ LLM call failed for {symbol}, using fallback HOLD")
            return {
                "action": "HOLD",
                "confidence": 0,
                "reason": "LLM call failed",
                "executable": False
            }
        
        # Extract fields with validation
        try:
            action = llm_response.get('action', 'HOLD').upper()
            confidence = float(llm_response.get('confidence', 0))
            reason = llm_response.get('reason', 'No reason provided')[:100]  # Limit length
            
            # Validate action
            if action not in ['BUY', 'SELL', 'HOLD']:
                logger.warning(f"⚠️ Invalid action '{action}', defaulting to HOLD")
                action = 'HOLD'
                confidence = 0
            
            # Clamp confidence to 0-100
            confidence = max(0, min(100, confidence))
            
            # Determine if signal is executable (confidence > 80 and action is not HOLD)
            executable = (action in ['BUY', 'SELL']) and (confidence > self.confidence_threshold)
            
            result = {
                "action": action,
                "confidence": confidence,
                "reason": reason,
                "executable": executable
            }
            
            if executable:
                logger.info(f"🎯 Executable signal: {action} {symbol} (Confidence: {confidence}%)")
            else:
                logger.debug(f"ℹ️ Non-executable signal: {action} {symbol} (Confidence: {confidence}%)")
            
            return result
            
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Failed to parse LLM response fields: {e}")
            return {
                "action": "HOLD",
                "confidence": 0,
                "reason": "Failed to parse LLM response",
                "executable": False
            }
    
    def get_market_sentiment(self, klines: List[List], 
                           past_trades: List[Dict[str, Any]]) -> str:
        """
        Generate market sentiment summary for heartbeat logging
        
        Args:
            klines: Recent candle data
            past_trades: Recent trade history
            
        Returns:
            Sentiment string
        """
        if not klines or len(klines) == 0:
            return "No market data available"
        
        # Calculate basic metrics
        try:
            current_price = float(klines[-1][4])
            
            # Price change over period
            if len(klines) > 1:
                start_price = float(klines[0][4])
                price_change_pct = ((current_price - start_price) / start_price) * 100
            else:
                price_change_pct = 0.0
            
            # Recent win rate
            if past_trades:
                recent_wins = sum(1 for t in past_trades if t.get('pnl', 0) > 0)
                win_rate = (recent_wins / len(past_trades)) * 100
            else:
                win_rate = 0.0
            
            # Generate sentiment
            trend = "bullish" if price_change_pct > 2 else "bearish" if price_change_pct < -2 else "neutral"
            
            sentiment = f"Price: ${current_price:.2f} ({price_change_pct:+.2f}%), Trend: {trend}, Recent Win Rate: {win_rate:.0f}%"
            
            return sentiment
            
        except (IndexError, ValueError) as e:
            logger.warning(f"Failed to generate sentiment: {e}")
            return "Unable to generate sentiment"
