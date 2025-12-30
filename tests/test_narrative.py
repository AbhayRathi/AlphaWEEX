"""
Unit Tests for Narrative Pulse
Tests whale monitoring and market narrative tracking
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.narrative import NarrativePulse
from data.shared_state import get_shared_state, RiskLevel


class TestNarrativePulse:
    """Test Narrative Pulse functionality"""
    
    def test_initialization(self):
        """Test Narrative Pulse initialization"""
        narrative = NarrativePulse(
            whale_threshold_btc=1000.0,
            dump_risk_duration_hours=24
        )
        
        assert narrative is not None
        assert narrative.whale_threshold_btc == 1000.0
        assert narrative.dump_risk_duration_hours == 24
    
    def test_whale_inflow_detection(self):
        """Test detection of whale inflows above threshold"""
        narrative = NarrativePulse(whale_threshold_btc=1000.0)
        
        # Test whale inflow (above threshold)
        result = narrative.check_whale_inflow(
            exchange_inflow_btc=1500.0,
            source="test"
        )
        
        assert result['is_whale_event'] is True
        assert result['whale_dump_risk'] is True
        assert result['exchange_inflow_btc'] == 1500.0
    
    def test_normal_inflow_detection(self):
        """Test detection of normal inflows below threshold"""
        narrative = NarrativePulse(whale_threshold_btc=1000.0)
        
        # Test normal inflow (below threshold)
        result = narrative.check_whale_inflow(
            exchange_inflow_btc=500.0,
            source="test"
        )
        
        assert result['is_whale_event'] is False
        assert result['exchange_inflow_btc'] == 500.0
    
    def test_whale_dump_risk_flag(self):
        """Test whale dump risk flag management"""
        narrative = NarrativePulse()
        
        # Initially no risk
        assert narrative.get_whale_dump_risk() is False
        
        # Trigger whale event
        narrative.check_whale_inflow(exchange_inflow_btc=1500.0)
        
        # Risk should be active
        assert narrative.get_whale_dump_risk() is True
    
    def test_shared_state_integration(self):
        """Test integration with SharedState"""
        narrative = NarrativePulse(whale_threshold_btc=1000.0)
        shared_state = get_shared_state()
        
        # Trigger whale event
        narrative.check_whale_inflow(exchange_inflow_btc=2000.0)
        
        # Check that shared state was updated
        oracle_data = shared_state.get_oracle_data()
        
        # Should have whale_dump_risk flag
        assert 'whale_dump_risk' in oracle_data['data']
        assert oracle_data['data']['whale_dump_risk'] is True
    
    def test_whale_events_tracking(self):
        """Test tracking of whale events"""
        narrative = NarrativePulse()
        
        # Generate multiple whale events
        narrative.check_whale_inflow(exchange_inflow_btc=1500.0)
        narrative.check_whale_inflow(exchange_inflow_btc=2000.0)
        narrative.check_whale_inflow(exchange_inflow_btc=1200.0)
        
        events = narrative.get_whale_events(limit=10)
        
        assert len(events) == 3
        assert all('inflow_btc' in event for event in events)
        assert all('timestamp' in event for event in events)
    
    def test_monitor_narrative(self):
        """Test comprehensive narrative monitoring"""
        narrative = NarrativePulse()
        
        market_data = {
            'price': 50000.0,
            'volume_24h': 200000.0,
            'price_change_pct': -6.0  # Significant drop
        }
        
        narrative_result = narrative.monitor_narrative(market_data)
        
        assert 'overall_sentiment' in narrative_result
        assert 'signals' in narrative_result
        assert 'whale_dump_risk' in narrative_result
        assert 'recommendation' in narrative_result
    
    def test_narrative_signals(self):
        """Test narrative signal generation"""
        narrative = NarrativePulse()
        
        # Market data with high volume and price dump
        market_data = {
            'price': 50000.0,
            'volume_24h': 150000.0,
            'price_change_pct': -7.0
        }
        
        result = narrative.monitor_narrative(market_data)
        
        # Should have signals
        assert len(result['signals']) > 0
        
        # Should detect price dump
        signal_types = [s['type'] for s in result['signals']]
        assert 'PRICE_DUMP' in signal_types
    
    def test_get_summary(self):
        """Test getting narrative summary"""
        narrative = NarrativePulse()
        
        # Trigger some whale events
        narrative.check_whale_inflow(exchange_inflow_btc=1500.0)
        narrative.check_whale_inflow(exchange_inflow_btc=800.0)
        
        summary = narrative.get_summary()
        
        assert 'whale_dump_risk' in summary
        assert 'whale_threshold_btc' in summary
        assert 'total_whale_events' in summary
        assert 'recent_whale_events' in summary


class TestNarrativeSentiments:
    """Test narrative sentiment classification"""
    
    def test_caution_sentiment(self):
        """Test CAUTION sentiment with multiple high severity signals"""
        narrative = NarrativePulse(whale_threshold_btc=500.0)
        
        market_data = {
            'price': 50000.0,
            'volume_24h': 200000.0,  # High volume (>100k triggers whale check)
            'price_change_pct': -8.0  # Significant dump
        }
        
        result = narrative.monitor_narrative(market_data)
        
        # Should be in CAUTION mode due to price dump
        assert result['overall_sentiment'] in ['CAUTION', 'WATCHFUL']
    
    def test_normal_sentiment(self):
        """Test NORMAL sentiment with no signals"""
        narrative = NarrativePulse(whale_threshold_btc=10000.0)
        
        market_data = {
            'price': 50000.0,
            'volume_24h': 50000.0,  # Normal volume
            'price_change_pct': 1.0  # Small positive change
        }
        
        result = narrative.monitor_narrative(market_data)
        
        # Should be in NORMAL mode
        assert result['overall_sentiment'] == 'NORMAL'
    
    def test_recommendation_generation(self):
        """Test recommendation generation based on sentiment"""
        narrative = NarrativePulse()
        
        # Test CAUTION recommendation
        caution_rec = narrative._get_recommendation('CAUTION')
        assert 'reduce' in caution_rec.lower() or 'tighten' in caution_rec.lower()
        
        # Test NORMAL recommendation
        normal_rec = narrative._get_recommendation('NORMAL')
        assert 'normal' in normal_rec.lower() or 'continue' in normal_rec.lower()


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_inflow(self):
        """Test handling of zero inflow"""
        narrative = NarrativePulse()
        
        result = narrative.check_whale_inflow(exchange_inflow_btc=0.0)
        
        assert result['is_whale_event'] is False
        assert result['whale_dump_risk'] is False
    
    def test_negative_inflow(self):
        """Test handling of negative inflow (outflow)"""
        narrative = NarrativePulse()
        
        result = narrative.check_whale_inflow(exchange_inflow_btc=-500.0)
        
        # Negative values should not trigger whale alert
        assert result['is_whale_event'] is False
    
    def test_custom_threshold(self):
        """Test custom whale threshold"""
        narrative = NarrativePulse(whale_threshold_btc=5000.0)
        
        # Below custom threshold
        result1 = narrative.check_whale_inflow(exchange_inflow_btc=3000.0)
        assert result1['is_whale_event'] is False
        
        # Above custom threshold
        result2 = narrative.check_whale_inflow(exchange_inflow_btc=6000.0)
        assert result2['is_whale_event'] is True
    
    def test_missing_market_data_fields(self):
        """Test handling of missing market data fields"""
        narrative = NarrativePulse()
        
        # Market data with missing fields
        market_data = {
            'price': 50000.0
            # Missing volume_24h and price_change_pct
        }
        
        # Should not crash, should handle gracefully
        result = narrative.monitor_narrative(market_data)
        
        assert 'overall_sentiment' in result
        assert isinstance(result, dict)


class TestRiskElevation:
    """Test risk level elevation due to whale activity"""
    
    def test_risk_elevation_on_whale_event(self):
        """Test that whale event elevates risk level to HIGH"""
        narrative = NarrativePulse(whale_threshold_btc=1000.0)
        shared_state = get_shared_state()
        
        # Set initial risk to NORMAL
        shared_state.set_global_risk_level(RiskLevel.NORMAL)
        
        # Trigger whale event
        narrative.check_whale_inflow(exchange_inflow_btc=2000.0)
        
        # Risk level should be elevated to HIGH
        current_risk = shared_state.get_global_risk_level()
        assert current_risk == RiskLevel.HIGH


def test_whale_inflow_integration():
    """
    Integration test: Verify whale inflow sets whale_dump_risk flag in SharedState
    """
    narrative = NarrativePulse(whale_threshold_btc=1000.0)
    shared_state = get_shared_state()
    
    print("🐋 Testing whale inflow detection...")
    
    # Mock exchange inflow > 1000 BTC
    result = narrative.check_whale_inflow(exchange_inflow_btc=1500.0, source="test")
    
    print(f"   Inflow: {result['exchange_inflow_btc']} BTC")
    print(f"   Threshold: {result['whale_threshold_btc']} BTC")
    print(f"   Whale Event: {result['is_whale_event']}")
    print(f"   Dump Risk: {result['whale_dump_risk']}")
    
    # Verify whale_dump_risk flag is set
    assert result['whale_dump_risk'] is True
    
    # Verify SharedState was updated
    oracle_data = shared_state.get_oracle_data()
    assert 'whale_dump_risk' in oracle_data['data']
    assert oracle_data['data']['whale_dump_risk'] is True
    
    print("   ✅ Test passed: Whale dump risk flag set in SharedState")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
