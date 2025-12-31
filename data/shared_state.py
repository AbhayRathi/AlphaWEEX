"""
Shared State for Global Risk Management
Maintains global risk level and sentiment information accessible across the system
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Global risk levels"""
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class SharedState:
    """
    Thread-safe shared state for global risk and sentiment
    
    Features:
    - Global risk level from TradFi Oracle
    - Sentiment multiplier from Sentiment Agent
    - Thread-safe access to shared data
    """
    
    def __init__(self):
        """Initialize SharedState"""
        self._lock = threading.Lock()
        self._global_risk_level = RiskLevel.NORMAL
        self._sentiment_multiplier = 1.0
        self._whale_dump_risk = False
        self._last_oracle_update: Optional[datetime] = None
        self._last_sentiment_update: Optional[datetime] = None
        self._oracle_data: Dict[str, Any] = {}
        self._sentiment_data: Dict[str, Any] = {}
        
    def set_global_risk_level(self, level: RiskLevel, oracle_data: Optional[Dict[str, Any]] = None):
        """
        Set global risk level (thread-safe)
        
        Args:
            level: Risk level (NORMAL or HIGH)
            oracle_data: Optional oracle data (SPY/QQQ metrics)
        """
        with self._lock:
            old_level = self._global_risk_level
            self._global_risk_level = level
            self._last_oracle_update = datetime.now()
            if oracle_data:
                self._oracle_data = oracle_data
            
            if old_level != level:
                logger.info(f"🚨 Global risk level changed: {old_level} -> {level}")
            else:
                logger.debug(f"Global risk level updated: {level}")
    
    def get_global_risk_level(self) -> RiskLevel:
        """
        Get current global risk level (thread-safe)
        
        Returns:
            Current risk level
        """
        with self._lock:
            return self._global_risk_level
    
    def set_sentiment_multiplier(self, multiplier: float, sentiment_data: Optional[Dict[str, Any]] = None):
        """
        Set sentiment multiplier (thread-safe)
        
        Args:
            multiplier: Sentiment multiplier (0.5 to 1.5)
            sentiment_data: Optional sentiment analysis data
        """
        # Clamp multiplier to valid range
        multiplier = max(0.5, min(1.5, multiplier))
        
        with self._lock:
            self._sentiment_multiplier = multiplier
            self._last_sentiment_update = datetime.now()
            if sentiment_data:
                self._sentiment_data = sentiment_data
            
            logger.info(f"💭 Sentiment multiplier updated: {multiplier:.2f}")
    
    def get_sentiment_multiplier(self) -> float:
        """
        Get current sentiment multiplier (thread-safe)
        
        Returns:
            Current sentiment multiplier
        """
        with self._lock:
            return self._sentiment_multiplier
    
    def get_oracle_data(self) -> Dict[str, Any]:
        """
        Get latest oracle data (thread-safe)
        
        Returns:
            Dictionary with oracle metrics
        """
        with self._lock:
            return {
                'risk_level': self._global_risk_level,
                'last_update': self._last_oracle_update.isoformat() if self._last_oracle_update else None,
                'data': self._oracle_data.copy()
            }
    
    def get_sentiment_data(self) -> Dict[str, Any]:
        """
        Get latest sentiment data (thread-safe)
        
        Returns:
            Dictionary with sentiment metrics
        """
        with self._lock:
            return {
                'multiplier': self._sentiment_multiplier,
                'last_update': self._last_sentiment_update.isoformat() if self._last_sentiment_update else None,
                'data': self._sentiment_data.copy()
            }
    
    def set_whale_dump_risk(self, risk_active: bool):
        """
        Set whale dump risk flag (thread-safe)
        
        Args:
            risk_active: Whether whale dump risk is active
        """
        with self._lock:
            old_risk = self._whale_dump_risk
            self._whale_dump_risk = risk_active
            if old_risk != risk_active:
                logger.warning(f"🐋 Whale dump risk: {risk_active}")
    
    def get_whale_dump_risk(self) -> bool:
        """
        Get whale dump risk flag (thread-safe)
        
        Returns:
            Current whale dump risk status
        """
        with self._lock:
            return self._whale_dump_risk
    
    def get_all_state(self) -> Dict[str, Any]:
        """
        Get complete state snapshot (thread-safe)
        
        Returns:
            Dictionary with all state information
        """
        with self._lock:
            return {
                'global_risk_level': self._global_risk_level,
                'sentiment_multiplier': self._sentiment_multiplier,
                'whale_dump_risk': self._whale_dump_risk,
                'last_oracle_update': self._last_oracle_update.isoformat() if self._last_oracle_update else None,
                'last_sentiment_update': self._last_sentiment_update.isoformat() if self._last_sentiment_update else None,
                'oracle_data': self._oracle_data.copy(),
                'sentiment_data': self._sentiment_data.copy()
            }


# Global singleton instance
_shared_state_instance: Optional[SharedState] = None


def get_shared_state() -> SharedState:
    """
    Get or create the global SharedState singleton
    
    Returns:
        SharedState instance
    """
    global _shared_state_instance
    if _shared_state_instance is None:
        _shared_state_instance = SharedState()
    return _shared_state_instance
