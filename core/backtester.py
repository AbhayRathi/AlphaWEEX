"""
Vectorized Backtester for AlphaWEEX
Pandas-based backtesting engine with performance metrics
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import importlib.util
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorizedBacktester:
    """
    Vectorized Backtesting Engine
    
    Features:
    - Pandas-based vectorized operations for speed
    - Loads data from data/market_cache/ CSV files
    - Tests active_logic.py versions
    - Calculates Sharpe Ratio and Max Drawdown
    - Enforces deployment thresholds (Sharpe > 1.2, Max DD < 5%)
    """
    
    # Deployment thresholds
    MIN_SHARPE_RATIO = 1.2
    MAX_DRAWDOWN_THRESHOLD = 0.05  # 5%
    
    def __init__(self, data_directory: str = "data/market_cache"):
        """
        Initialize Vectorized Backtester
        
        Args:
            data_directory: Directory containing market data CSV files
        """
        self.data_directory = Path(data_directory)
        self.results_cache: Dict[str, Any] = {}
        
    def load_market_data(self, symbol: str = "BTC_USDT") -> pd.DataFrame:
        """
        Load market data from CSV file
        
        Args:
            symbol: Trading symbol (default: BTC_USDT)
            
        Returns:
            DataFrame with OHLCV data and timestamp index
        """
        csv_path = self.data_directory / f"{symbol}.csv"
        
        if not csv_path.exists():
            logger.warning(f"Market data file not found: {csv_path}")
            logger.info("Generating sample data...")
            return self._generate_sample_data()
        
        try:
            df = pd.read_csv(csv_path)
            
            # Ensure required columns exist
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV must contain columns: {required_columns}")
            
            # Convert timestamp to datetime and set as index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Loaded {len(df)} candles from {csv_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading market data: {str(e)}")
            logger.info("Generating sample data...")
            return self._generate_sample_data()
    
    def _generate_sample_data(self, num_candles: int = 1000) -> pd.DataFrame:
        """
        Generate sample OHLCV data for testing
        
        Args:
            num_candles: Number of candles to generate
            
        Returns:
            DataFrame with synthetic OHLCV data
        """
        logger.info(f"Generating {num_candles} candles of sample data...")
        
        # Generate timestamps (15-minute intervals)
        start_time = pd.Timestamp.now() - pd.Timedelta(minutes=15 * num_candles)
        timestamps = pd.date_range(start=start_time, periods=num_candles, freq='15min')
        
        # Generate realistic price action with trend and noise
        base_price = 40000
        trend = np.linspace(0, 5000, num_candles)
        volatility = np.random.randn(num_candles) * 500
        closes = base_price + trend + volatility
        
        # Generate OHLC from closes
        opens = closes + np.random.randn(num_candles) * 100
        highs = np.maximum(opens, closes) + np.abs(np.random.randn(num_candles) * 150)
        lows = np.minimum(opens, closes) - np.abs(np.random.randn(num_candles) * 150)
        
        # Generate volume
        base_volume = 100
        volumes = base_volume + np.abs(np.random.randn(num_candles) * 50)
        
        df = pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        }, index=timestamps)
        
        return df
    
    def load_strategy_module(self, logic_file_path: str = "active_logic.py"):
        """
        Load trading strategy module dynamically
        
        Args:
            logic_file_path: Path to the strategy file
            
        Returns:
            Loaded module object
        """
        try:
            spec = importlib.util.spec_from_file_location("strategy_module", logic_file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules["strategy_module"] = module
                spec.loader.exec_module(module)
                logger.info(f"Loaded strategy module from {logic_file_path}")
                return module
            else:
                raise ImportError(f"Could not load module from {logic_file_path}")
        except Exception as e:
            logger.error(f"Error loading strategy module: {str(e)}")
            return None
    
    def run_backtest(
        self,
        logic_file_path: str = "active_logic.py",
        initial_capital: float = 10000.0,
        symbol: str = "BTC_USDT"
    ) -> Dict[str, Any]:
        """
        Run backtest on a strategy file
        
        Args:
            logic_file_path: Path to active_logic.py (or version)
            initial_capital: Starting capital for backtest
            symbol: Trading symbol
            
        Returns:
            Dictionary with backtest results and metrics
        """
        logger.info(f"🔬 Running backtest on {logic_file_path}...")
        
        # Load market data
        df = self.load_market_data(symbol)
        if df.empty:
            return self._error_result("No market data available")
        
        # Load strategy module
        strategy = self.load_strategy_module(logic_file_path)
        if not strategy:
            return self._error_result("Failed to load strategy module")
        
        # Verify required functions exist
        if not hasattr(strategy, 'calculate_indicators') or not hasattr(strategy, 'generate_signal'):
            return self._error_result("Strategy missing required functions")
        
        # Run vectorized backtest
        try:
            results = self._execute_vectorized_backtest(
                df, strategy, initial_capital
            )
            
            # Calculate performance metrics
            metrics = self._calculate_metrics(results, initial_capital)
            
            # Check deployment thresholds
            can_deploy = (
                metrics['sharpe_ratio'] >= self.MIN_SHARPE_RATIO and
                metrics['max_drawdown'] <= self.MAX_DRAWDOWN_THRESHOLD
            )
            
            logger.info(f"📊 Backtest Results:")
            logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f} (threshold: {self.MIN_SHARPE_RATIO})")
            logger.info(f"   Max Drawdown: {metrics['max_drawdown']:.2%} (threshold: {self.MAX_DRAWDOWN_THRESHOLD:.2%})")
            logger.info(f"   Total Return: {metrics['total_return']:.2%}")
            logger.info(f"   Win Rate: {metrics['win_rate']:.2%}")
            logger.info(f"   Can Deploy: {'✅ YES' if can_deploy else '❌ NO'}")
            
            return {
                'success': True,
                'can_deploy': can_deploy,
                'metrics': metrics,
                'equity_curve': results['equity'],
                'trades': results['trades'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during backtest execution: {str(e)}")
            return self._error_result(str(e))
    
    def _execute_vectorized_backtest(
        self,
        df: pd.DataFrame,
        strategy,
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Execute vectorized backtest using pandas operations
        
        Args:
            df: OHLCV DataFrame
            strategy: Strategy module with calculate_indicators and generate_signal
            initial_capital: Starting capital
            
        Returns:
            Dictionary with equity curve and trade history
        """
        # Convert DataFrame to list format for strategy compatibility
        ohlcv_list = []
        for idx, row in df.iterrows():
            ohlcv_list.append([
                int(idx.timestamp() * 1000),  # timestamp in ms
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume']
            ])
        
        # Initialize tracking variables
        equity = initial_capital
        position = 0.0  # BTC position size
        cash = initial_capital
        equity_curve = []
        trades = []
        
        # Iterate through candles
        for i in range(20, len(ohlcv_list)):  # Start at 20 for indicator warmup
            # Get data window
            window = ohlcv_list[:i+1]
            
            # Calculate indicators
            try:
                indicators = strategy.calculate_indicators(window)
            except Exception as e:
                logger.warning(f"Indicator calculation failed at candle {i}: {str(e)}")
                continue
            
            # Generate signal (pass mock analysis for compatibility)
            mock_analysis = {
                'signal': 'HOLD',
                'confidence': 0.5,
                'regime': 'UNKNOWN'
            }
            
            try:
                signal = strategy.generate_signal(indicators, mock_analysis)
            except Exception as e:
                logger.warning(f"Signal generation failed at candle {i}: {str(e)}")
                continue
            
            # Get current price
            current_price = ohlcv_list[i][4]  # close price
            
            # Execute trades based on signal
            action = signal.get('action', 'HOLD')
            confidence = signal.get('confidence', 0.0)
            
            # Only trade if confidence is high enough
            if confidence > 0.6:
                if action == 'BUY' and position == 0:
                    # Buy with 95% of cash (leave 5% for fees)
                    buy_amount = cash * 0.95
                    position = buy_amount / current_price
                    cash = cash * 0.05
                    trades.append({
                        'timestamp': df.index[i],
                        'action': 'BUY',
                        'price': current_price,
                        'size': position,
                        'value': buy_amount
                    })
                    
                elif action == 'SELL' and position > 0:
                    # Sell entire position
                    sell_value = position * current_price * 0.95  # 5% fee
                    cash += sell_value
                    trades.append({
                        'timestamp': df.index[i],
                        'action': 'SELL',
                        'price': current_price,
                        'size': position,
                        'value': sell_value
                    })
                    position = 0
            
            # Calculate current equity
            equity = cash + (position * current_price)
            equity_curve.append({
                'timestamp': df.index[i],
                'equity': equity,
                'position': position,
                'cash': cash
            })
        
        return {
            'equity': equity_curve,
            'trades': trades
        }
    
    def _calculate_metrics(
        self,
        results: Dict[str, Any],
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from backtest results
        
        Args:
            results: Backtest results with equity curve
            initial_capital: Starting capital
            
        Returns:
            Dictionary of performance metrics
        """
        equity_curve = results['equity']
        trades = results['trades']
        
        if not equity_curve:
            return self._default_metrics()
        
        # Convert to DataFrame for easier calculation
        equity_df = pd.DataFrame(equity_curve)
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # Total return
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital
        
        # Sharpe Ratio (annualized, assuming 15-minute data)
        # Trading days per year: 252, periods per day: 24 * 4 = 96
        # Annualization factor: sqrt(252 * 96) = sqrt(24192) ≈ 155.5
        returns_mean = equity_df['returns'].mean()
        returns_std = equity_df['returns'].std()
        
        if returns_std > 0:
            sharpe_ratio = (returns_mean / returns_std) * np.sqrt(24192)
        else:
            sharpe_ratio = 0.0
        
        # Max Drawdown
        running_max = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Win Rate
        if len(trades) >= 2:
            winning_trades = 0
            for i in range(0, len(trades) - 1, 2):
                if i + 1 < len(trades):
                    buy_trade = trades[i] if trades[i]['action'] == 'BUY' else trades[i+1]
                    sell_trade = trades[i+1] if trades[i+1]['action'] == 'SELL' else trades[i]
                    if sell_trade['value'] > buy_trade['value']:
                        winning_trades += 1
            win_rate = winning_trades / (len(trades) / 2) if len(trades) > 0 else 0
        else:
            win_rate = 0.0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': len(trades),
            'final_equity': final_equity
        }
    
    def _default_metrics(self) -> Dict[str, Any]:
        """Return default metrics for failed backtests"""
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 1.0,
            'win_rate': 0.0,
            'num_trades': 0,
            'final_equity': 0.0
        }
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            'success': False,
            'can_deploy': False,
            'error': error_message,
            'metrics': self._default_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_for_deployment(
        self,
        logic_file_path: str = "active_logic.py"
    ) -> Tuple[bool, str]:
        """
        Validate if a strategy meets deployment thresholds
        
        Args:
            logic_file_path: Path to strategy file
            
        Returns:
            Tuple of (can_deploy, reason)
        """
        result = self.run_backtest(logic_file_path)
        
        if not result['success']:
            return False, f"Backtest failed: {result.get('error', 'Unknown error')}"
        
        if not result['can_deploy']:
            metrics = result['metrics']
            reasons = []
            
            if metrics['sharpe_ratio'] < self.MIN_SHARPE_RATIO:
                reasons.append(
                    f"Sharpe Ratio {metrics['sharpe_ratio']:.2f} < {self.MIN_SHARPE_RATIO}"
                )
            
            if metrics['max_drawdown'] > self.MAX_DRAWDOWN_THRESHOLD:
                reasons.append(
                    f"Max Drawdown {metrics['max_drawdown']:.2%} > {self.MAX_DRAWDOWN_THRESHOLD:.2%}"
                )
            
            return False, "Deployment criteria not met: " + "; ".join(reasons)
        
        return True, "All deployment criteria met"
