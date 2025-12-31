"""
Shadow Trading Engine - Runs parallel high-risk strategies in memory
Compares Shadow ROI vs Live ROI and generates promotion alerts
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShadowStrategy:
    """
    Represents a shadow strategy with higher risk/leverage
    """
    
    def __init__(
        self,
        name: str,
        leverage_multiplier: float = 2.0,
        risk_multiplier: float = 1.5
    ):
        """
        Initialize Shadow Strategy
        
        Args:
            name: Strategy name
            leverage_multiplier: Leverage multiplier vs live strategy
            risk_multiplier: Risk multiplier vs live strategy
        """
        self.name = name
        self.leverage_multiplier = leverage_multiplier
        self.risk_multiplier = risk_multiplier
        self.roi_history: List[float] = []
        self.sharpe_history: List[float] = []
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0.0
    
    def record_trade(self, pnl: float, is_winner: bool, sharpe_ratio: float):
        """
        Record a trade result
        
        Args:
            pnl: Profit/Loss for the trade
            is_winner: Whether trade was profitable
            sharpe_ratio: Current Sharpe Ratio
        """
        self.trade_count += 1
        if is_winner:
            self.win_count += 1
        self.total_pnl += pnl
        
        # Calculate ROI
        roi = (pnl / 1000.0) * 100  # Assume $1000 base
        self.roi_history.append(roi)
        self.sharpe_history.append(sharpe_ratio)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get strategy statistics
        
        Returns:
            Dictionary with strategy stats
        """
        avg_roi = sum(self.roi_history) / len(self.roi_history) if self.roi_history else 0.0
        avg_sharpe = (
            sum(self.sharpe_history) / len(self.sharpe_history)
            if self.sharpe_history
            else 0.0
        )
        win_rate = (self.win_count / self.trade_count) if self.trade_count > 0 else 0.0
        
        return {
            'name': self.name,
            'leverage_multiplier': self.leverage_multiplier,
            'risk_multiplier': self.risk_multiplier,
            'trade_count': self.trade_count,
            'win_count': self.win_count,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'avg_roi': avg_roi,
            'avg_sharpe': avg_sharpe,
            'roi_history': self.roi_history[-10:],  # Last 10
            'sharpe_history': self.sharpe_history[-10:]  # Last 10
        }


class ShadowEngine:
    """
    Shadow Trading Engine: Runs parallel high-risk strategies in memory
    
    Features:
    - Maintains shadow strategy with higher risk/leverage
    - Compares Shadow ROI vs Live ROI
    - Tracks Sharpe Ratio over iterations
    - Generates promotion alerts when shadow outperforms
    """
    
    def __init__(
        self,
        promotion_threshold_iterations: int = 100,
        sharpe_ratio_threshold: float = 1.2
    ):
        """
        Initialize Shadow Engine
        
        Args:
            promotion_threshold_iterations: Iterations before promotion check
            sharpe_ratio_threshold: Minimum Sharpe Ratio for promotion
        """
        self.promotion_threshold_iterations = promotion_threshold_iterations
        self.sharpe_ratio_threshold = sharpe_ratio_threshold
        
        # Initialize shadow and live strategies
        self.shadow_strategy = ShadowStrategy(
            name="Shadow-HighRisk",
            leverage_multiplier=2.0,
            risk_multiplier=1.5
        )
        self.live_strategy = ShadowStrategy(
            name="Live-Standard",
            leverage_multiplier=1.0,
            risk_multiplier=1.0
        )
        
        self.promotion_alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        logger.info("🌑 Shadow Engine initialized")
    
    def simulate_trade_pair(
        self,
        market_signal: str,
        market_price: float,
        market_volatility: float = 0.02
    ) -> Dict[str, Any]:
        """
        Simulate a trade for both shadow and live strategies
        
        Args:
            market_signal: "buy", "sell", or "hold"
            market_price: Current market price
            market_volatility: Market volatility (default: 2%)
            
        Returns:
            Simulation results
        """
        import random
        
        with self._lock:
            # Simulate live strategy trade
            live_pnl = self._simulate_single_trade(
                market_signal,
                market_price,
                self.live_strategy.leverage_multiplier,
                market_volatility
            )
            live_is_winner = live_pnl > 0
            live_sharpe = self._calculate_sharpe_ratio(self.live_strategy)
            
            self.live_strategy.record_trade(live_pnl, live_is_winner, live_sharpe)
            
            # Simulate shadow strategy trade (higher risk/reward)
            shadow_pnl = self._simulate_single_trade(
                market_signal,
                market_price,
                self.shadow_strategy.leverage_multiplier,
                market_volatility * self.shadow_strategy.risk_multiplier
            )
            shadow_is_winner = shadow_pnl > 0
            shadow_sharpe = self._calculate_sharpe_ratio(self.shadow_strategy)
            
            self.shadow_strategy.record_trade(shadow_pnl, shadow_is_winner, shadow_sharpe)
            
            # Check for promotion alert
            promotion_alert = None
            if self.shadow_strategy.trade_count >= self.promotion_threshold_iterations:
                promotion_alert = self._check_promotion_criteria()
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'market_signal': market_signal,
                'live_pnl': live_pnl,
                'live_sharpe': live_sharpe,
                'shadow_pnl': shadow_pnl,
                'shadow_sharpe': shadow_sharpe,
                'promotion_alert': promotion_alert
            }
            
            return result
    
    def _simulate_single_trade(
        self,
        signal: str,
        price: float,
        leverage: float,
        volatility: float
    ) -> float:
        """
        Simulate a single trade outcome
        
        Args:
            signal: Trading signal
            price: Market price
            leverage: Leverage multiplier
            volatility: Market volatility
            
        Returns:
            Simulated PnL
        """
        import random
        
        if signal == "hold":
            return 0.0
        
        # Simulate price movement
        # Positive bias for correct signals, negative for wrong signals
        base_move = random.gauss(0, volatility)
        
        if signal == "buy":
            # Assume bullish bias in buy signal
            price_move = base_move + (volatility * 0.3)  # Slight bullish bias
        elif signal == "sell":
            # Assume bearish bias in sell signal
            price_move = base_move - (volatility * 0.3)  # Slight bearish bias
        else:
            price_move = base_move
        
        # Calculate PnL with leverage
        base_position_size = 1000.0  # $1000 base
        pnl = (price_move * price) * leverage * (base_position_size / price)
        
        return pnl
    
    def _calculate_sharpe_ratio(self, strategy: ShadowStrategy) -> float:
        """
        Calculate Sharpe Ratio for a strategy
        
        Args:
            strategy: Strategy to calculate Sharpe for
            
        Returns:
            Sharpe Ratio
        """
        if len(strategy.roi_history) < 2:
            return 0.0
        
        import statistics
        
        # Use recent history (last 30 trades)
        recent_returns = strategy.roi_history[-30:]
        
        if len(recent_returns) < 2:
            return 0.0
        
        avg_return = statistics.mean(recent_returns)
        std_return = statistics.stdev(recent_returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe (assuming daily returns)
        sharpe = (avg_return / std_return) * (252 ** 0.5)
        
        return sharpe
    
    def _check_promotion_criteria(self) -> Optional[Dict[str, Any]]:
        """
        Check if shadow strategy meets promotion criteria
        
        Returns:
            Promotion alert if criteria met, None otherwise
        """
        # Get current stats
        shadow_stats = self.shadow_strategy.get_stats()
        live_stats = self.live_strategy.get_stats()
        
        shadow_sharpe = shadow_stats['avg_sharpe']
        live_sharpe = live_stats['avg_sharpe']
        
        # Check if shadow maintains higher Sharpe for threshold iterations
        if (
            shadow_sharpe > live_sharpe
            and shadow_sharpe >= self.sharpe_ratio_threshold
            and self.shadow_strategy.trade_count >= self.promotion_threshold_iterations
        ):
            alert = {
                'timestamp': datetime.now().isoformat(),
                'type': 'PROMOTION_ALERT',
                'message': (
                    f"🌟 Shadow strategy outperforms Live! "
                    f"Shadow Sharpe: {shadow_sharpe:.2f} > Live Sharpe: {live_sharpe:.2f} "
                    f"over {self.shadow_strategy.trade_count} iterations"
                ),
                'shadow_stats': shadow_stats,
                'live_stats': live_stats,
                'recommendation': 'Consider promoting Shadow strategy to Live'
            }
            
            self.promotion_alerts.append(alert)
            logger.warning(alert['message'])
            
            # Reset counters for next evaluation cycle
            self.shadow_strategy.trade_count = 0
            self.live_strategy.trade_count = 0
            
            return alert
        
        return None
    
    def get_comparison_summary(self) -> Dict[str, Any]:
        """
        Get comparison summary between shadow and live strategies
        
        Returns:
            Comparison statistics
        """
        with self._lock:
            shadow_stats = self.shadow_strategy.get_stats()
            live_stats = self.live_strategy.get_stats()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'shadow': shadow_stats,
                'live': live_stats,
                'comparison': {
                    'roi_diff': shadow_stats['avg_roi'] - live_stats['avg_roi'],
                    'sharpe_diff': shadow_stats['avg_sharpe'] - live_stats['avg_sharpe'],
                    'win_rate_diff': shadow_stats['win_rate'] - live_stats['win_rate'],
                    'shadow_outperforms': shadow_stats['avg_sharpe'] > live_stats['avg_sharpe']
                },
                'promotion_alerts_count': len(self.promotion_alerts),
                'latest_promotion_alert': (
                    self.promotion_alerts[-1] if self.promotion_alerts else None
                )
            }
    
    def reset_shadow_strategy(
        self,
        leverage_multiplier: float = 2.0,
        risk_multiplier: float = 1.5
    ):
        """
        Reset shadow strategy with new parameters
        
        Args:
            leverage_multiplier: New leverage multiplier
            risk_multiplier: New risk multiplier
        """
        with self._lock:
            self.shadow_strategy = ShadowStrategy(
                name=f"Shadow-HighRisk-v{len(self.promotion_alerts) + 1}",
                leverage_multiplier=leverage_multiplier,
                risk_multiplier=risk_multiplier
            )
            logger.info(
                f"🔄 Shadow strategy reset: "
                f"leverage={leverage_multiplier}x, risk={risk_multiplier}x"
            )
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data formatted for dashboard display
        
        Returns:
            Dashboard-friendly data
        """
        comparison = self.get_comparison_summary()
        
        return {
            'shadow_roi': comparison['shadow']['avg_roi'],
            'live_roi': comparison['live']['avg_roi'],
            'shadow_sharpe': comparison['shadow']['avg_sharpe'],
            'live_sharpe': comparison['live']['avg_sharpe'],
            'shadow_trades': comparison['shadow']['trade_count'],
            'iterations_to_promotion': (
                self.promotion_threshold_iterations - comparison['shadow']['trade_count']
            ),
            'promotion_alert_active': (
                comparison['shadow']['avg_sharpe'] > comparison['live']['avg_sharpe']
                and comparison['shadow']['trade_count'] >= self.promotion_threshold_iterations
            ),
            'latest_alert': comparison['latest_promotion_alert']
        }
