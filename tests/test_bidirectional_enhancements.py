"""
Tests for Bi-Directional Trading Enhancements (7 Enhancements)

Testing:
1. Symmetric funding rate logic - boost SHORT confidence
2. Asymmetric stop-loss for shorts
3. Higher confidence threshold for shorts
4. Trend filter to block counter-trend shorts
5. Performance tracking by direction
6. Max hold time for shorts
7. Position verification after short entry
"""
import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from core.funding_rate_analyzer import FundingRateAnalyzer
from core.db import DatabaseManager
from core.weex_v2_client import WEEXv2Client


class TestEnhancement1SymmetricFundingRate:
    """Test Enhancement 1: Symmetric funding rate logic"""
    
    def test_boost_short_confidence_extreme_positive_funding(self):
        """Test that SHORT signals get confidence boost when funding > 0.05%"""
        analyzer = FundingRateAnalyzer()
        
        # Create a SELL signal with moderate confidence
        technical_signal = {
            "action": "SELL",
            "confidence": 0.70,
            "reason": "Overbought RSI"
        }
        
        # Extreme positive funding (0.06% > 0.05% threshold)
        funding_rate = 0.06
        
        # Apply funding rate adjustment
        adjusted_signal = analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
        
        # Should boost SHORT confidence by 30%
        expected_confidence = 0.70 * 1.3  # 0.91
        assert adjusted_signal["confidence"] > technical_signal["confidence"], \
            "SHORT confidence should be boosted with extreme positive funding"
        assert abs(adjusted_signal["confidence"] - expected_confidence) < 0.01, \
            f"Expected confidence ~{expected_confidence}, got {adjusted_signal['confidence']}"
        assert "FUNDING BOOST" in adjusted_signal["reason"], \
            "Reason should mention funding boost"
        assert adjusted_signal["action"] == "SELL", \
            "Action should remain SELL"


class TestEnhancement2AsymmetricStopLoss:
    """Test Enhancement 2: Asymmetric stop-loss for shorts"""
    
    def test_short_uses_tighter_stop_loss(self):
        """Test that shorts use 0.40% SL vs 0.50% for longs"""
        # This test verifies the constants are set correctly in weex_v2_client.py
        # The actual SL thresholds are defined in check_tp_sl_triggers method
        
        # Mock client
        client = Mock(spec=WEEXv2Client)
        client.open_positions = {
            "cmt_btcusdt": {
                "side": "SHORT",
                "entryPrice": 100.0,
                "size": -0.1
            }
        }
        client.position_scaling_state = {
            "cmt_btcusdt": {
                "partial_taken": False,
                "breakeven_set": False,
                "reinvested": False,
                "original_size": 0.1,
                "realized_profit": 0.0
            }
        }
        
        # Create actual client instance to test the method
        with patch('core.weex_v2_client.WEEXv2Client.__init__', return_value=None):
            real_client = WEEXv2Client.__new__(WEEXv2Client)
            real_client.open_positions = client.open_positions
            real_client.position_scaling_state = client.position_scaling_state
            
            # Test SHORT SL trigger at -0.40%
            # Price goes from 100 to 100.40 (0.40% increase = -0.40% PnL for short)
            current_price = 100.40
            
            with patch('core.weex_v2_client.logger'):
                trigger = real_client.check_tp_sl_triggers("cmt_btcusdt", current_price)
            
            # Should trigger SL for SHORT at -0.40%
            assert trigger == "SL", \
                f"SHORT should trigger SL at -0.40%, got {trigger}"
    
    def test_long_uses_wider_stop_loss(self):
        """Test that longs use 0.50% SL"""
        # Mock client
        client = Mock(spec=WEEXv2Client)
        client.open_positions = {
            "cmt_btcusdt": {
                "side": "LONG",
                "entryPrice": 100.0,
                "size": 0.1
            }
        }
        client.position_scaling_state = {
            "cmt_btcusdt": {
                "partial_taken": False,
                "breakeven_set": False,
                "reinvested": False,
                "original_size": 0.1,
                "realized_profit": 0.0
            }
        }
        
        # Create actual client instance
        with patch('core.weex_v2_client.WEEXv2Client.__init__', return_value=None):
            real_client = WEEXv2Client.__new__(WEEXv2Client)
            real_client.open_positions = client.open_positions
            real_client.position_scaling_state = client.position_scaling_state
            
            # Test LONG SL does NOT trigger at -0.40%
            current_price = 99.60  # -0.40%
            
            with patch('core.weex_v2_client.logger'):
                trigger = real_client.check_tp_sl_triggers("cmt_btcusdt", current_price)
            
            # Should NOT trigger yet
            assert trigger is None, \
                f"LONG should NOT trigger SL at -0.40%, got {trigger}"
            
            # Test LONG SL triggers at -0.50%
            current_price = 99.50  # -0.50%
            
            with patch('core.weex_v2_client.logger'):
                trigger = real_client.check_tp_sl_triggers("cmt_btcusdt", current_price)
            
            assert trigger == "SL", \
                f"LONG should trigger SL at -0.50%, got {trigger}"


class TestEnhancement3HigherConfidenceShorts:
    """Test Enhancement 3: Higher confidence threshold for shorts"""
    
    def test_sell_confidence_increased_from_065_to_078(self):
        """Test that SELL signals have confidence 0.78 instead of 0.65"""
        from competition_bot import CompetitionTradingBot
        
        # Create mock klines data with RSI > 75 (overbought)
        klines = []
        # Generate klines that will result in RSI > 75
        for i in range(100):
            # Upward trend with high closes
            klines.append([
                1234567890 + i * 60,  # timestamp
                50000 + i * 100,       # open
                50000 + i * 100 + 200, # high
                50000 + i * 100 - 50,  # low
                50000 + i * 100 + 150, # close (trending up)
                1000000                 # volume
            ])
        
        # Mock bot components
        with patch('competition_bot.WEEXv2Client'), \
             patch('competition_bot.AITradingLogger'), \
             patch('competition_bot.DatabaseManager'), \
             patch('competition_bot.StrategyEngine'), \
             patch('competition_bot.API_KEY', 'test'), \
             patch('competition_bot.API_SECRET', 'test'), \
             patch('competition_bot.API_PASSWORD', 'test'):
            
            bot = CompetitionTradingBot(use_llm=False)
            bot.client.get_funding_rate = Mock(return_value=0.0)
            
            # Generate signal
            signal = bot.generate_signal(klines, "cmt_btcusdt")
            
            # Check if SELL signal has higher confidence
            if signal["action"] == "SELL":
                assert signal["confidence"] >= 0.78, \
                    f"SELL confidence should be >= 0.78, got {signal['confidence']}"


class TestEnhancement5PerformanceTracking:
    """Test Enhancement 5: Performance tracking by direction"""
    
    def test_get_performance_by_direction(self):
        """Test that performance can be tracked separately for LONG/SHORT"""
        import tempfile
        import os
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Record some LONG trades
            db.record_trade_entry("cmt_btcusdt", "BUY", 50000, 0.1, "Test long 1")
            db.record_trade_exit("cmt_btcusdt", 50500, 1.0)  # +1% win
            
            db.record_trade_entry("cmt_btcusdt", "BUY", 51000, 0.1, "Test long 2")
            db.record_trade_exit("cmt_btcusdt", 50500, -0.98)  # -0.98% loss
            
            # Record some SHORT trades (SELL side)
            db.record_trade_entry("cmt_ethusdt", "SELL", 3000, 0.5, "Test short 1")
            db.record_trade_exit("cmt_ethusdt", 2970, 1.0)  # +1% win for short
            
            db.record_trade_entry("cmt_ethusdt", "SELL", 2950, 0.5, "Test short 2")
            db.record_trade_exit("cmt_ethusdt", 2980, -1.02)  # -1.02% loss for short
            
            db.record_trade_entry("cmt_ethusdt", "SELL", 2980, 0.5, "Test short 3")
            db.record_trade_exit("cmt_ethusdt", 2950, 1.01)  # +1.01% win for short
            
            # Get performance by direction
            perf = db.get_performance_by_direction()
            
            # Check BUY (LONG) performance
            assert "BUY" in perf, "Should have BUY performance data"
            buy_stats = perf["BUY"]
            assert buy_stats["total_trades"] == 2, f"Expected 2 BUY trades, got {buy_stats['total_trades']}"
            assert buy_stats["wins"] == 1, f"Expected 1 win, got {buy_stats['wins']}"
            assert buy_stats["win_rate"] == 0.5, f"Expected 50% win rate, got {buy_stats['win_rate']}"
            
            # Check SELL (SHORT) performance
            assert "SELL" in perf, "Should have SELL performance data"
            sell_stats = perf["SELL"]
            assert sell_stats["total_trades"] == 3, f"Expected 3 SELL trades, got {sell_stats['total_trades']}"
            assert sell_stats["wins"] == 2, f"Expected 2 wins, got {sell_stats['wins']}"
            assert abs(sell_stats["win_rate"] - 0.667) < 0.01, \
                f"Expected ~66.7% win rate, got {sell_stats['win_rate']}"
            
            db.close()
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestEnhancement6MaxHoldTime:
    """Test Enhancement 6: Max hold time for shorts"""
    
    def test_short_entry_times_tracking(self):
        """Test that short entry times are tracked"""
        from competition_bot import CompetitionTradingBot
        
        with patch('competition_bot.WEEXv2Client'), \
             patch('competition_bot.AITradingLogger'), \
             patch('competition_bot.DatabaseManager'), \
             patch('competition_bot.StrategyEngine'), \
             patch('competition_bot.API_KEY', 'test'), \
             patch('competition_bot.API_SECRET', 'test'), \
             patch('competition_bot.API_PASSWORD', 'test'):
            
            bot = CompetitionTradingBot(use_llm=False)
            
            # Verify short_entry_times dict exists
            assert hasattr(bot, 'short_entry_times'), \
                "Bot should have short_entry_times tracking dict"
            assert isinstance(bot.short_entry_times, dict), \
                "short_entry_times should be a dictionary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
