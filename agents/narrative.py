"""
Narrative Pulse - Monitors whale activity and market narratives
Tracks whale inflows and sets risk flags in SharedState
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from data.shared_state import get_shared_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NarrativePulse:
    """
    Narrative Pulse: Monitors whale activity and market narratives
    
    Features:
    - Track whale inflows to exchanges
    - Monitor large BTC transfers
    - Set whale_dump_risk flag in SharedState
    - Generate narrative-based alerts
    """
    
    def __init__(
        self,
        whale_threshold_btc: float = 1000.0,
        dump_risk_duration_hours: int = 24
    ):
        """
        Initialize Narrative Pulse
        
        Args:
            whale_threshold_btc: BTC threshold for whale alert (default: 1000 BTC)
            dump_risk_duration_hours: How long to maintain dump risk flag
        """
        self.whale_threshold_btc = whale_threshold_btc
        self.dump_risk_duration_hours = dump_risk_duration_hours
        self.shared_state = get_shared_state()
        self.whale_events: List[Dict[str, Any]] = []
        self._whale_dump_risk = False
        
        logger.info(
            f"📡 Narrative Pulse initialized "
            f"(whale threshold: {whale_threshold_btc} BTC)"
        )
    
    def check_whale_inflow(
        self,
        exchange_inflow_btc: float,
        source: str = "mock"
    ) -> Dict[str, Any]:
        """
        Check for whale inflows to exchanges
        
        Args:
            exchange_inflow_btc: Amount of BTC flowing into exchanges
            source: Data source (e.g., "mock", "glassnode", "cryptoquant")
            
        Returns:
            Analysis result with whale_dump_risk flag
        """
        timestamp = datetime.now()
        
        # Check if inflow exceeds whale threshold
        is_whale_event = exchange_inflow_btc > self.whale_threshold_btc
        
        if is_whale_event:
            logger.warning(
                f"🐋 WHALE ALERT: {exchange_inflow_btc:.2f} BTC inflow detected "
                f"(threshold: {self.whale_threshold_btc} BTC)"
            )
            
            # Set whale dump risk flag in SharedState
            self._whale_dump_risk = True
            self.shared_state.set_whale_dump_risk(True)
            
            # Record whale event
            whale_event = {
                'timestamp': timestamp.isoformat(),
                'inflow_btc': exchange_inflow_btc,
                'threshold': self.whale_threshold_btc,
                'source': source,
                'risk_level': 'HIGH' if exchange_inflow_btc > self.whale_threshold_btc * 2 else 'MEDIUM'
            }
            self.whale_events.append(whale_event)
            
            # Update SharedState with whale dump risk
            self._update_shared_state_whale_risk(True, whale_event)
            
        else:
            logger.info(
                f"✅ Normal inflow: {exchange_inflow_btc:.2f} BTC "
                f"(below {self.whale_threshold_btc} BTC threshold)"
            )
            
            # If no whale event, consider clearing the risk flag
            # (in production, use time-based decay)
            if self._whale_dump_risk:
                # For simplicity, clear flag if consecutive normal readings
                self._whale_dump_risk = False
                self.shared_state.set_whale_dump_risk(False)
                self._update_shared_state_whale_risk(False, None)
        
        result = {
            'timestamp': timestamp.isoformat(),
            'exchange_inflow_btc': exchange_inflow_btc,
            'whale_threshold_btc': self.whale_threshold_btc,
            'is_whale_event': is_whale_event,
            'whale_dump_risk': self._whale_dump_risk,
            'source': source
        }
        
        return result
    
    def _update_shared_state_whale_risk(
        self,
        risk_active: bool,
        whale_event: Optional[Dict[str, Any]]
    ):
        """
        Update SharedState with whale dump risk flag
        
        Args:
            risk_active: Whether whale dump risk is active
            whale_event: Whale event details if applicable
        """
        # Get current state
        current_state = self.shared_state.get_all_state()
        
        # Add whale_dump_risk to state
        # Note: SharedState doesn't have a native whale_dump_risk field,
        # so we store it in oracle_data for now
        oracle_data = current_state.get('oracle_data', {})
        oracle_data['whale_dump_risk'] = risk_active
        
        if whale_event:
            oracle_data['whale_event'] = whale_event
        
        # Update state (storing in oracle_data as metadata)
        from data.shared_state import RiskLevel
        current_risk = self.shared_state.get_global_risk_level()
        
        # If whale risk is active, ensure risk level is at least HIGH
        if risk_active and current_risk == RiskLevel.NORMAL:
            logger.warning("🐋 Elevating risk level to HIGH due to whale inflow")
            self.shared_state.set_global_risk_level(RiskLevel.HIGH, oracle_data)
        else:
            # Just update oracle data without changing risk level
            self.shared_state.set_global_risk_level(current_risk, oracle_data)
    
    def get_whale_dump_risk(self) -> bool:
        """
        Get current whale dump risk status
        
        Returns:
            True if whale dump risk is active, False otherwise
        """
        return self._whale_dump_risk
    
    def get_whale_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent whale events
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent whale events
        """
        return self.whale_events[-limit:]
    
    def monitor_narrative(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Monitor market narrative based on multiple signals
        
        Args:
            market_data: Market data including volume, price, etc.
            
        Returns:
            Narrative analysis
        """
        # Extract metrics from market data
        price = market_data.get('price', 0)
        volume_24h = market_data.get('volume_24h', 0)
        price_change_pct = market_data.get('price_change_pct', 0)
        
        # Mock exchange inflow (in production, fetch from Glassnode/CryptoQuant)
        # For demonstration, simulate based on volume
        simulated_exchange_inflow = volume_24h * 0.001  # 0.1% of volume as inflow
        
        # Check whale inflow
        whale_check = self.check_whale_inflow(
            simulated_exchange_inflow,
            source="simulated"
        )
        
        # Build narrative
        narrative_signals = []
        
        if whale_check['is_whale_event']:
            narrative_signals.append({
                'type': 'WHALE_INFLOW',
                'severity': 'HIGH',
                'message': f"Large BTC inflow detected: {simulated_exchange_inflow:.2f} BTC"
            })
        
        if price_change_pct < -5:
            narrative_signals.append({
                'type': 'PRICE_DUMP',
                'severity': 'HIGH',
                'message': f"Significant price drop: {price_change_pct:.2f}%"
            })
        elif price_change_pct > 5:
            narrative_signals.append({
                'type': 'PRICE_PUMP',
                'severity': 'MEDIUM',
                'message': f"Significant price increase: {price_change_pct:.2f}%"
            })
        
        if volume_24h > 100000:  # Example threshold
            narrative_signals.append({
                'type': 'HIGH_VOLUME',
                'severity': 'MEDIUM',
                'message': f"High trading volume: {volume_24h:.0f}"
            })
        
        # Determine overall narrative
        if any(signal['severity'] == 'HIGH' for signal in narrative_signals):
            overall_sentiment = 'CAUTION'
        elif len(narrative_signals) > 0:
            overall_sentiment = 'WATCHFUL'
        else:
            overall_sentiment = 'NORMAL'
        
        narrative = {
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': overall_sentiment,
            'signals': narrative_signals,
            'whale_dump_risk': self._whale_dump_risk,
            'whale_check': whale_check,
            'recommendation': self._get_recommendation(overall_sentiment)
        }
        
        logger.info(
            f"📡 Narrative: {overall_sentiment} "
            f"({len(narrative_signals)} signals detected)"
        )
        
        return narrative
    
    def _get_recommendation(self, sentiment: str) -> str:
        """
        Get trading recommendation based on narrative sentiment
        
        Args:
            sentiment: Overall market sentiment
            
        Returns:
            Trading recommendation
        """
        recommendations = {
            'CAUTION': 'Reduce position sizes and tighten stop-losses',
            'WATCHFUL': 'Monitor closely and be ready to reduce exposure',
            'NORMAL': 'Continue normal trading operations'
        }
        
        return recommendations.get(sentiment, 'Continue normal trading operations')
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of narrative pulse status
        
        Returns:
            Summary dictionary
        """
        return {
            'whale_dump_risk': self._whale_dump_risk,
            'whale_threshold_btc': self.whale_threshold_btc,
            'total_whale_events': len(self.whale_events),
            'recent_whale_events': self.get_whale_events(limit=5),
            'shared_state_updated': True
        }
