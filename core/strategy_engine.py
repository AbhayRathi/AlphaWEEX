"""
LLM-Based Strategy Engine for Autonomous Trading Decisions

Supports multiple LLM providers: DeepSeek, OpenAI, and Anthropic.
"""
from dotenv import load_dotenv
import json
import logging
import os
import time
import re
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime

load_dotenv()  

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

# Type hint for BehavioralAdversary (to avoid circular import)
try:
    from agents.adversary import BehavioralAdversary
    BehavioralAdversaryType = BehavioralAdversary
except ImportError:
    BehavioralAdversaryType = Any  # Fallback if import fails


class LLMCircuitBreaker:
    """
    Circuit breaker pattern for LLM failures
    
    Prevents cascading failures by temporarily disabling LLM calls
    after repeated failures.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout_minutes: int = 15):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_minutes: Minutes to wait before attempting retry
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_minutes * 60
        self.failures = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.timeout_seconds
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                logger.info("Circuit breaker: Attempting reset (HALF_OPEN)")
                self.state = 'HALF_OPEN'
            else:
                raise Exception(f"Circuit breaker OPEN: Too many LLM failures. Retry in {self.timeout_seconds - (time.time() - self.last_failure_time):.0f}s")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset circuit breaker on success"""
        if self.state == 'HALF_OPEN':
            logger.info("Circuit breaker: Reset successful (CLOSED)")
        self.failures = 0
        self.state = 'CLOSED'
        self.last_failure_time = None
    
    def _on_failure(self):
        """Record failure and potentially open circuit"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            logger.error(f"Circuit breaker: OPEN after {self.failures} failures")
            self.state = 'OPEN'
        else:
            logger.warning(f"Circuit breaker: Failure {self.failures}/{self.failure_threshold}")


class StrategyEngine:
    """
    LLM-powered trading strategy engine
    
    Features:
    - DeepSeek integration (recommended for cost-effectiveness)
    - OpenAI GPT-4 integration
    - Anthropic Claude integration
    - Context-aware prompting with market data
    - Trade history memory integration
    - JSON response parsing
    - Token usage tracking
    - Circuit breaker for failure protection
    """
    
    def __init__(self, provider: Optional[Literal["openai", "anthropic", "deepseek"]] = None,
                 api_key: Optional[str] = None, model: Optional[str] = None,
                 base_url: Optional[str] = None, 
                 behavioral_adversary: Optional[BehavioralAdversaryType] = None):
        """
        Initialize Strategy Engine
        
        Args:
            provider: LLM provider ("openai", "anthropic", or "deepseek"). If None, auto-detects from environment.
            api_key: API key for the LLM provider. If None, uses environment variable matching provider.
            model: Model name (optional, uses defaults)
            base_url: Base URL for API (optional, defaults to https://api.deepseek.com for DeepSeek)
            behavioral_adversary: Optional BehavioralAdversary instance for psychology tags
            
        Note:
            Auto-detection priority (when provider=None): DeepSeek > OpenAI > Anthropic
            When provider is specified but api_key is None, only that provider's env var is checked.
        """
        # Auto-detect provider from environment if not specified
        if provider is None:
            # Check providers in priority order: DeepSeek > OpenAI > Anthropic
            provider_priority = [
                ("deepseek", os.getenv('DEEPSEEK_API_KEY')),
                ("openai", os.getenv('OPENAI_API_KEY')),
                ("anthropic", os.getenv('ANTHROPIC_API_KEY'))
            ]
            
            for prov_name, prov_key in provider_priority:
                if prov_key:
                    provider = prov_name
                    api_key = api_key or prov_key
                    break
            else:
                raise ValueError("No LLM provider specified. Set provider parameter or environment variable (DEEPSEEK_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
        
        # If provider is specified but api_key is not, get it from environment
        if api_key is None:
            if provider:  # Defensive check
                api_key = os.getenv(f'{provider.upper()}_API_KEY')
            if not api_key:
                raise ValueError(f"No LLM API key found for {provider}. Set {provider.upper()}_API_KEY environment variable or pass api_key parameter.")
        
        self.provider = provider
        self.api_key = api_key
        self.behavioral_adversary = behavioral_adversary
        
        # Set default models
        if model:
            self.model = model
        elif provider == "openai":
            self.model = "gpt-4o-mini"  # Cost-effective and fast
        elif provider == "anthropic":
            self.model = "claude-3-5-sonnet-20241022"
        elif provider == "deepseek":
            self.model = "deepseek-reasoner"  # For trading decisions
        else:
            self.model = None
        
        # Validate provider availability
        if provider in ["openai", "deepseek"] and not OPENAI_AVAILABLE:
            raise ImportError("OpenAI not installed. Install with: pip install openai")
        if provider == "anthropic" and not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic not installed. Install with: pip install anthropic")
        
        # Initialize client
        if provider == "openai":
            self.client = openai.OpenAI(api_key=api_key)
        elif provider == "deepseek":
            # DeepSeek uses OpenAI SDK with custom base_url
            self.base_url = base_url or "https://api.deepseek.com"
            self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)
        
        # Initialize circuit breaker
        self.circuit_breaker = LLMCircuitBreaker(failure_threshold=5, timeout_minutes=15)
        
        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        self.total_cost_usd = 0.0
        
        # Heartbeat model for DeepSeek (use deepseek-chat for lighter queries)
        self.heartbeat_model = "deepseek-chat" if provider == "deepseek" else self.model
        
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
                     leverage: int = 20, current_price: float = 0.0) -> str:
        """
        Build the complete prompt for LLM (Aether-Evo Engine format)
        
        Args:
            symbol: Trading symbol
            klines: Market K-lines data
            performance: Recent performance metrics
            balance: Current balance in USDT
            leverage: Trading leverage
            current_price: Current market price
            
        Returns:
            Complete prompt string
        """
        candles_data = self._format_candles_data(klines)
        trade_history = self._format_trade_history(performance)
        
        # Get behavioral psychology tags from BehavioralAdversary if available
        behavioral_tags = "No behavioral analysis available"
        if self.behavioral_adversary:
            try:
                market_data = {
                    'price': current_price,
                    'rsi': self._calculate_rsi_from_klines(klines),
                    'volume': float(klines[-1][5]) if klines and len(klines[-1]) > 5 else 0.0,
                    'price_change_pct': ((float(klines[-1][4]) - float(klines[0][4])) / float(klines[0][4]) * 100) if klines and len(klines) > 1 else 0.0
                }
                psychology = self.behavioral_adversary.analyze_psychology(market_data)
                behavioral_tags = f"{psychology.get('detected_archetype', 'NEUTRAL')} (Confidence: {psychology.get('confidence', 0.5):.2%}, Signal: {psychology.get('signal', 'HOLD')})"
            except Exception as e:
                logger.warning(f"Failed to get behavioral tags: {str(e)}")
        
        # Aether-Evo Engine prompt format
        prompt = f"""You are the Aether-Evo Engine. An elite AI trading system with access to market data, behavioral psychology, and performance history.

DATA:
- Symbol: {symbol}
- Balance: ${balance:.2f} USDT
- Leverage: {leverage}x
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[100m Candles]:
{candles_data}

[Psychology]: {behavioral_tags}

[Past Perf]:
{trade_history}

TASK:
Analyze the data and make a trading decision. Consider:
1. Market momentum and price action patterns
2. Behavioral psychology (FOMO, Panic, Revenge, Liquidity Hunter)
3. Our trading history (learn from successes and failures)
4. Risk management with {leverage}x leverage

RESPONSE FORMAT (JSON only):
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0-100,
    "reasoning": "Max 20 words explaining the decision"
}}

Be concise. Protect capital. Execute only high-probability setups."""
        
        return prompt
    
    def _calculate_rsi_from_klines(self, klines: List[List], period: int = 14) -> float:
        """Calculate RSI from klines data"""
        if not klines or len(klines) < period + 1:
            return 50.0
        
        closes = [float(candle[4]) for candle in klines]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _call_openai(self, prompt: str, use_reasoner: bool = True) -> Dict[str, Any]:
        """
        Call OpenAI/DeepSeek API with token tracking
        
        Args:
            prompt: Prompt text
            use_reasoner: Use deepseek-reasoner model (only for DeepSeek)
            
        Returns:
            Parsed response dictionary
        """
        try:
            start_time = time.time()
            
            # Select model based on provider and context
            model = self.model
            if self.provider == "deepseek" and not use_reasoner:
                model = self.heartbeat_model
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are the Aether-Evo Engine, an expert cryptocurrency trader. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Track token usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            self.total_calls += 1
            
            # Estimate cost based on provider
            if self.provider == "deepseek":
                # DeepSeek pricing: $0.27/1M input, $1.10/1M output for reasoner
                # DeepSeek-chat: $0.14/1M input, $0.28/1M output
                if model == "deepseek-reasoner":
                    input_cost = (usage.prompt_tokens / 1_000_000) * 0.27
                    output_cost = (usage.completion_tokens / 1_000_000) * 1.10
                else:
                    input_cost = (usage.prompt_tokens / 1_000_000) * 0.14
                    output_cost = (usage.completion_tokens / 1_000_000) * 0.28
            else:
                # GPT-4o-mini pricing: $0.15/1M input, $0.60/1M output
                input_cost = (usage.prompt_tokens / 1_000_000) * 0.15
                output_cost = (usage.completion_tokens / 1_000_000) * 0.60
            
            call_cost = input_cost + output_cost
            self.total_cost_usd += call_cost
            
            logger.info(f"🤖 {self.provider.upper()} call ({model}): {latency_ms:.0f}ms, {usage.prompt_tokens} in + {usage.completion_tokens} out tokens, ${call_cost:.4f}")
            
            content = response.choices[0].message.content
            
            # Extract JSON from response (handle both plain JSON and markdown-wrapped)
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks using regex
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                else:
                    # Fallback: try to find JSON object
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        content = match.group(0)
                parsed = json.loads(content)
            
            # Normalize confidence to 0-1 if it's 0-100
            if 'confidence' in parsed and parsed['confidence'] > 1.0:
                parsed['confidence'] = parsed['confidence'] / 100.0
            
            return parsed
            
        except Exception as e:
            logger.error(f"{self.provider.upper()} API error: {str(e)}")
            raise
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """
        Call Anthropic API with token tracking
        
        Args:
            prompt: Prompt text
            
        Returns:
            Parsed response dictionary
        """
        try:
            start_time = time.time()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Track token usage
            usage = response.usage
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens
            self.total_calls += 1
            
            # Estimate cost (Claude 3.5 Sonnet pricing: $3/1M input, $15/1M output)
            input_cost = (usage.input_tokens / 1_000_000) * 3.0
            output_cost = (usage.output_tokens / 1_000_000) * 15.0
            call_cost = input_cost + output_cost
            self.total_cost_usd += call_cost
            
            logger.info(f"🤖 Anthropic call: {latency_ms:.0f}ms, {usage.input_tokens} in + {usage.output_tokens} out tokens, ${call_cost:.4f}")
            
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
        Get trading decision from LLM with circuit breaker protection
        
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
            # Get current price from klines
            current_price = float(klines[-1][4]) if klines and len(klines) > 0 else 0.0
            
            # Build prompt
            prompt = self._build_prompt(symbol, klines, performance, balance, leverage, current_price)
            
            # Call LLM with circuit breaker protection
            def _make_llm_call():
                if self.provider in ["openai", "deepseek"]:
                    return self._call_openai(prompt, use_reasoner=True)
                elif self.provider == "anthropic":
                    return self._call_anthropic(prompt)
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")
            
            response = self.circuit_breaker.call(_make_llm_call)
            
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
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get LLM usage statistics
        
        Returns:
            Dictionary with token usage and cost metrics
        """
        avg_input = self.total_input_tokens / self.total_calls if self.total_calls > 0 else 0
        avg_output = self.total_output_tokens / self.total_calls if self.total_calls > 0 else 0
        avg_cost = self.total_cost_usd / self.total_calls if self.total_calls > 0 else 0
        
        return {
            "provider": self.provider,
            "model": self.model,
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "avg_input_tokens": avg_input,
            "avg_output_tokens": avg_output,
            "avg_cost_per_call": avg_cost,
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": self.circuit_breaker.failures
        }
    
    def generate_heartbeat_sentiment(self, symbol: str, klines: List[List], 
                                     current_equity: float) -> str:
        """
        Generate market sentiment for heartbeat logging using lighter model
        
        Args:
            symbol: Trading symbol
            klines: Market K-lines data
            current_equity: Current total equity in USDT
            
        Returns:
            Market sentiment string
        """
        try:
            if not klines or len(klines) == 0:
                return "No market data available"
            
            current_price = float(klines[-1][4])
            
            # Use DeepSeek-chat for heartbeat (lighter/cheaper)
            if self.provider == "deepseek":
                prompt = f"""Brief market analysis for {symbol} at ${current_price:.2f}. 
Total equity: ${current_equity:.2f}. 
Recent candles: {len(klines)} data points.
Provide 1 sentence market view."""
                
                try:
                    response = self._call_openai(prompt, use_reasoner=False)
                    return response.get("response") or response.get("content") or response.get("reasoning") or f"Monitoring {symbol} at ${current_price:.2f}"
                except Exception as e:
                    logger.debug(f"DeepSeek heartbeat call failed: {e}")
                    # We don't return here so it naturally hits the fallback below
            
            # Fallback to simple description
            return f"{symbol} at ${current_price:.2f}, Equity: ${current_equity:.2f}"
            
        except Exception as e:
            logger.warning(f"Failed to generate heartbeat sentiment: {str(e)}")
            return f"Monitoring {symbol}"
