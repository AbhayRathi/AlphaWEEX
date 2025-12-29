"""
Sentiment Agent - Analyzes market sentiment from Fear & Greed Index and news
Uses R1 reasoning to classify sentiment and generate multipliers
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not installed. Sentiment agent will use fallback mode.")

from data.shared_state import get_shared_state


class SentimentAgent:
    """
    Sentiment Agent: Analyzes market sentiment
    
    Features:
    - Fetch Fear & Greed Index from alternative.me API
    - Fetch latest Bitcoin news headlines
    - Use R1 reasoning to classify sentiment
    - Generate sentiment multiplier (0.5 to 1.5)
    """
    
    def __init__(
        self,
        deepseek_api_key: Optional[str] = None,
        use_deepseek: bool = False
    ):
        """
        Initialize Sentiment Agent
        
        Args:
            deepseek_api_key: DeepSeek API key for R1 analysis (or from env)
            use_deepseek: Whether to use DeepSeek R1 for analysis (False = rule-based)
        """
        self.deepseek_api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.use_deepseek = use_deepseek and bool(self.deepseek_api_key)
        self.shared_state = get_shared_state()
        
        if self.use_deepseek:
            logger.info("✅ Sentiment Agent initialized with DeepSeek R1")
        else:
            logger.info("✅ Sentiment Agent initialized with rule-based analysis")
    
    def fetch_fear_greed_index(self) -> Dict[str, Any]:
        """
        Fetch Fear & Greed Index from alternative.me API
        
        Returns:
            Dictionary with Fear & Greed data
        """
        if not REQUESTS_AVAILABLE:
            return self._get_fallback_fear_greed()
        
        try:
            response = requests.get(
                "https://api.alternative.me/fng/",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                fng_data = data['data'][0]
                
                result = {
                    'value': int(fng_data['value']),
                    'classification': fng_data['value_classification'],
                    'timestamp': fng_data['timestamp'],
                    'source': 'alternative.me'
                }
                
                logger.info(
                    f"😱 Fear & Greed Index: {result['value']} ({result['classification']})"
                )
                
                return result
            else:
                logger.warning("Invalid Fear & Greed API response")
                return self._get_fallback_fear_greed()
                
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {str(e)}")
            return self._get_fallback_fear_greed()
    
    def _get_fallback_fear_greed(self) -> Dict[str, Any]:
        """
        Get fallback Fear & Greed data
        
        Returns:
            Neutral Fear & Greed data
        """
        return {
            'value': 50,
            'classification': 'Neutral',
            'timestamp': str(int(datetime.now().timestamp())),
            'source': 'fallback'
        }
    
    def fetch_bitcoin_news(self, count: int = 5) -> List[str]:
        """
        Fetch latest Bitcoin news headlines
        
        In production, this would fetch from CryptoPanic or similar API.
        For now, returns mock headlines or fetches from a simple source.
        
        Args:
            count: Number of headlines to fetch
            
        Returns:
            List of news headlines
        """
        # Mock headlines for demonstration
        # In production, integrate with CryptoPanic API or similar
        mock_headlines = [
            "Bitcoin holds steady above $95,000 as institutional interest grows",
            "Major banks announce blockchain integration plans",
            "Regulatory clarity expected in Q1 2024",
            "Bitcoin network hash rate reaches all-time high",
            "Analysts predict continued volatility in crypto markets"
        ]
        
        logger.info(f"📰 Fetched {len(mock_headlines)} Bitcoin headlines")
        return mock_headlines[:count]
    
    async def analyze_sentiment_with_r1(self, headlines: List[str], fear_greed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment using DeepSeek R1 reasoning
        
        Args:
            headlines: List of news headlines
            fear_greed: Fear & Greed Index data
            
        Returns:
            Sentiment analysis with multiplier
        """
        # R1 Prompt for sentiment analysis
        prompt = f"""Analyze these Bitcoin market indicators and classify the overall sentiment:

Fear & Greed Index: {fear_greed['value']} ({fear_greed['classification']})

Recent Headlines:
{chr(10).join(f"- {h}" for h in headlines)}

Task: Classify the overall market sentiment as one of:
- Euphoric (very bullish, overheated)
- Neutral (balanced market)
- Panicked (very bearish, fear-driven)

Based on your classification, provide a position size multiplier:
- Euphoric: 0.5-0.7 (reduce exposure due to overheating)
- Neutral: 0.9-1.1 (normal exposure)
- Panicked: 0.5-0.8 (reduce exposure due to fear)

Output your response as JSON with these fields:
- sentiment: "Euphoric" | "Neutral" | "Panicked"
- multiplier: float between 0.5 and 1.5
- reasoning: brief explanation

Example: {{"sentiment": "Neutral", "multiplier": 1.0, "reasoning": "Balanced market with steady growth"}}
"""
        
        # In a real implementation, call DeepSeek R1 API here
        # For now, use rule-based fallback
        logger.info("Using rule-based sentiment analysis (DeepSeek R1 integration pending)")
        return self._rule_based_sentiment(fear_greed, headlines)
    
    def _rule_based_sentiment(self, fear_greed: Dict[str, Any], headlines: List[str]) -> Dict[str, Any]:
        """
        Rule-based sentiment analysis (fallback)
        
        Args:
            fear_greed: Fear & Greed Index data
            headlines: List of news headlines
            
        Returns:
            Sentiment analysis with multiplier
        """
        fng_value = fear_greed['value']
        
        # Classify based on Fear & Greed Index
        if fng_value >= 75:
            sentiment = "Euphoric"
            multiplier = 0.6  # Reduce exposure when market is greedy
            reasoning = f"Extreme Greed (FNG: {fng_value}) - reducing position sizes"
        elif fng_value >= 55:
            sentiment = "Neutral"
            multiplier = 1.0  # Normal exposure
            reasoning = f"Greed (FNG: {fng_value}) - normal positioning"
        elif fng_value >= 45:
            sentiment = "Neutral"
            multiplier = 1.0  # Normal exposure
            reasoning = f"Neutral (FNG: {fng_value}) - normal positioning"
        elif fng_value >= 25:
            sentiment = "Neutral"
            multiplier = 0.9  # Slightly reduce in fear
            reasoning = f"Fear (FNG: {fng_value}) - slightly cautious"
        else:
            sentiment = "Panicked"
            multiplier = 0.7  # Reduce exposure during panic
            reasoning = f"Extreme Fear (FNG: {fng_value}) - reducing position sizes"
        
        # Adjust based on headline sentiment (simple keyword analysis)
        positive_keywords = ['bullish', 'growth', 'gains', 'surge', 'rally', 'positive', 'integration']
        negative_keywords = ['crash', 'plunge', 'bearish', 'decline', 'losses', 'fear', 'volatility']
        
        headlines_text = ' '.join(headlines).lower()
        positive_count = sum(1 for kw in positive_keywords if kw in headlines_text)
        negative_count = sum(1 for kw in negative_keywords if kw in headlines_text)
        
        if positive_count > negative_count + 1:
            multiplier = min(multiplier + 0.1, 1.5)
            reasoning += " | Positive news sentiment"
        elif negative_count > positive_count + 1:
            multiplier = max(multiplier - 0.1, 0.5)
            reasoning += " | Negative news sentiment"
        
        return {
            'sentiment': sentiment,
            'multiplier': round(multiplier, 2),
            'reasoning': reasoning,
            'fear_greed_value': fng_value
        }
    
    async def update_sentiment(self) -> float:
        """
        Update sentiment multiplier in shared state
        
        Returns:
            Sentiment multiplier (0.5 to 1.5)
        """
        try:
            # Fetch Fear & Greed Index
            fear_greed = self.fetch_fear_greed_index()
            
            # Fetch Bitcoin news
            headlines = self.fetch_bitcoin_news(count=5)
            
            # Analyze sentiment
            if self.use_deepseek:
                analysis = await self.analyze_sentiment_with_r1(headlines, fear_greed)
            else:
                analysis = self._rule_based_sentiment(fear_greed, headlines)
            
            multiplier = analysis['multiplier']
            
            # Update shared state
            sentiment_data = {
                'sentiment': analysis['sentiment'],
                'multiplier': multiplier,
                'reasoning': analysis['reasoning'],
                'fear_greed': fear_greed,
                'headlines': headlines,
                'timestamp': datetime.now().isoformat()
            }
            
            self.shared_state.set_sentiment_multiplier(multiplier, sentiment_data)
            
            logger.info(
                f"💭 Sentiment: {analysis['sentiment']} | "
                f"Multiplier: {multiplier:.2f} | "
                f"Reasoning: {analysis['reasoning']}"
            )
            
            return multiplier
            
        except Exception as e:
            logger.error(f"Error updating sentiment: {str(e)}")
            logger.warning("Defaulting to neutral sentiment (1.0)")
            
            # Default to neutral on error
            self.shared_state.set_sentiment_multiplier(
                1.0,
                {
                    'sentiment': 'Neutral',
                    'multiplier': 1.0,
                    'reasoning': f'Error fallback: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return 1.0
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """
        Get current sentiment summary
        
        Returns:
            Dictionary with sentiment summary
        """
        sentiment_data = self.shared_state.get_sentiment_data()
        
        return {
            'multiplier': sentiment_data['multiplier'],
            'last_update': sentiment_data['last_update'],
            'data': sentiment_data['data']
        }
