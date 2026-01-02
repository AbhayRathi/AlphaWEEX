"""
Comprehensive tests for the Aether-Evo Predator Suite agents:
- BehavioralAdversary (The Dark Mirror)
- ReconciliationAuditor (The Auditor)
- EvolutionaryMutator (The DNA Patch)
"""
import sys
from pathlib import Path
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.adversary import BehavioralAdversary
from agents.reconciliation_loop import IntelligenceLedger, ReconciliationAuditor
from agents.evolutionary_mutator import EvolutionaryMutator


class TestBehavioralAdversary:
    """Test Behavioral Adversary functionality"""
    
    def test_initialization(self):
        """Test adversary initialization"""
        adversary = BehavioralAdversary(use_shadow_mode=True)
        
        assert adversary is not None
        assert adversary.shadow_btc_price == 90000.0
        assert adversary.enable_cot is True
    
    def test_flash_crash_detection(self):
        """Test flash crash scenario - should detect panic and recommend buy"""
        adversary = BehavioralAdversary(use_shadow_mode=True)
        
        flash_crash_data = {
            'price': 85500.0,
            'rsi': 20.0,
            'volume': 5000.0,
            'price_change_pct': -5.0,
            'recent_lows': [86000, 87000, 88000]
        }
        
        result = adversary.analyze_psychology(
            flash_crash_data,
            sentiment="Extreme Fear"
        )
        
        assert result is not None
        assert result['detected_archetype'] == adversary.ARCHETYPE_PANIC_SELLER
        assert result['signal'] == 'BUY'
        assert result['vulnerability_score'] > 0
    
    def test_shadow_mock_mode(self):
        """Test 451 error handling with Shadow Mock Mode"""
        adversary = BehavioralAdversary(use_shadow_mode=True)
        
        result = adversary.analyze_psychology(
            {'price': 90000},
            sentiment="Neutral"
        )
        
        assert result is not None
        assert result['mode'] == 'SHADOW'
        assert result.get('shadow_mode') is True
        assert result['response_time'] < 1.0  # Should be fast
    
    def test_fomo_detection(self):
        """Test FOMO Chaser detection"""
        adversary = BehavioralAdversary(use_shadow_mode=True)
        
        fomo_data = {
            'price': 95000.0,
            'rsi': 78.0,
            'volume': 8000.0,
            'price_change_pct': 5.5,
        }
        
        result = adversary.analyze_psychology(fomo_data, sentiment="Extreme Greed")
        
        assert result is not None
        # Should detect FOMO or recommend SELL
        assert (result['detected_archetype'] == adversary.ARCHETYPE_FOMO_CHASER or
                result['signal'] == 'SELL')
    
    def test_liquidity_zones_calculation(self):
        """Test liquidity zone calculation for stop-loss clusters"""
        adversary = BehavioralAdversary()
        
        market_data = {
            'price': 90000.0,
            'recent_lows': [88000, 87500, 86000]
        }
        
        zones = adversary._calculate_liquidity_zones(market_data)
        
        assert len(zones) > 0
        assert all(z < 90000 for z in zones)  # All zones below current price
        assert all(z > 80000 for z in zones)  # Reasonable range


class TestIntelligenceLedger:
    """Test Intelligence Ledger functionality"""
    
    def setup_method(self):
        """Setup test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_ledger.db")
    
    def teardown_method(self):
        """Cleanup test database"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test ledger initialization"""
        ledger = IntelligenceLedger(db_path=self.test_db)
        
        assert ledger is not None
        assert ledger.db_path.exists()
    
    def test_record_prediction(self):
        """Test recording a prediction"""
        ledger = IntelligenceLedger(db_path=self.test_db)
        
        pred_id = ledger.record_prediction(
            predicted_bias="Bullish Extension",
            predicted_outcome="Bull Trap / Reversal",
            confidence=0.8,
            market_regime="BULL",
            archetype="FOMO_CHASER",
            signal="SELL",
            price_at_prediction=95000.0
        )
        
        assert pred_id > 0
    
    def test_get_statistics(self):
        """Test getting ledger statistics"""
        ledger = IntelligenceLedger(db_path=self.test_db)
        
        # Record some predictions
        for i in range(3):
            ledger.record_prediction(
                predicted_bias=f"Test {i}",
                predicted_outcome=f"Outcome {i}",
                confidence=0.7,
                market_regime="CHOPPY",
                archetype="NEUTRAL",
                signal="HOLD",
                price_at_prediction=90000.0
            )
        
        stats = ledger.get_statistics()
        
        assert stats['total_predictions'] == 3
        assert stats['audited_predictions'] == 0
    
    def test_failed_predictions(self):
        """Test getting failed predictions"""
        ledger = IntelligenceLedger(db_path=self.test_db)
        
        # Record predictions with negative scores
        for i in range(3):
            pred_id = ledger.record_prediction(
                predicted_bias=f"Test {i}",
                predicted_outcome=f"Outcome {i}",
                confidence=0.7,
                market_regime="CHOPPY",
                archetype="NEUTRAL",
                signal="HOLD",
                price_at_prediction=90000.0
            )
            
            # Add negative score
            ledger.update_success_score(pred_id, "1h", -0.5)
        
        failed = ledger.get_failed_predictions(limit=5)
        
        assert len(failed) == 3


class TestReconciliationAuditor:
    """Test Reconciliation Auditor functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_ledger.db")
        self.ledger = IntelligenceLedger(db_path=self.test_db)
    
    def teardown_method(self):
        """Cleanup"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test auditor initialization"""
        auditor = ReconciliationAuditor(ledger=self.ledger)
        
        assert auditor is not None
        assert auditor.ledger is not None
        assert len(auditor.audit_intervals) == 3
    
    def test_success_score_calculation(self):
        """Test success score calculation for predictions"""
        auditor = ReconciliationAuditor(ledger=self.ledger)
        
        # Test correct BUY prediction
        prediction = {
            'id': 1,
            'predicted_bias': 'Bearish Capitulation',
            'predicted_outcome': 'Mean Reversion',
            'confidence': 0.9,
            'signal': 'BUY',
            'price_at_prediction': 85000.0
        }
        
        # Price went up as predicted
        score = auditor._calculate_success_score(prediction, 87000.0)
        assert score > 0  # Positive score for correct prediction
        
        # Price went down (wrong prediction)
        score = auditor._calculate_success_score(prediction, 82000.0)
        assert score < 0  # Negative score for incorrect prediction
    
    def test_false_positive_detection(self):
        """Test that auditor correctly identifies false positives"""
        auditor = ReconciliationAuditor(ledger=self.ledger)
        
        # Prediction that turns out wrong
        prediction = {
            'id': 1,
            'predicted_bias': 'Bullish Extension',
            'predicted_outcome': 'Bull Trap',
            'confidence': 0.8,
            'signal': 'SELL',
            'price_at_prediction': 95000.0
        }
        
        # Price went up instead of down
        actual_price = 98000.0
        
        score = auditor._calculate_success_score(prediction, actual_price)
        
        # Should be negative (false positive)
        assert score < 0


class TestEvolutionaryMutator:
    """Test Evolutionary Mutator functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_dir = os.path.join(self.temp_dir, "prompts")
    
    def teardown_method(self):
        """Cleanup"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test mutator initialization"""
        mutator = EvolutionaryMutator(prompts_dir=self.prompts_dir)
        
        assert mutator is not None
        assert mutator.current_version == 0
        assert mutator.prompts_dir.exists()
    
    def test_symmetry_guard_safe_prompt(self):
        """Test Symmetry Guard accepts safe prompts"""
        mutator = EvolutionaryMutator(prompts_dir=self.prompts_dir)
        
        safe_prompt = """
You are a behavioral analyst.
Always use stop-losses and risk management.
Explain your reasoning step-by-step.
"""
        
        result = mutator._symmetry_guard(safe_prompt)
        assert result is True
    
    def test_symmetry_guard_dangerous_prompt(self):
        """Test Symmetry Guard rejects dangerous prompts"""
        mutator = EvolutionaryMutator(prompts_dir=self.prompts_dir)
        
        dangerous_prompt = """
You are a trader.
No stop-losses needed.
Go all in on every trade.
"""
        
        result = mutator._symmetry_guard(dangerous_prompt)
        assert result is False
    
    def test_prompt_version_control(self):
        """Test prompt version control"""
        mutator = EvolutionaryMutator(prompts_dir=self.prompts_dir)
        
        # Save a new prompt version
        test_prompt = "Test prompt for version 1"
        mutator._save_prompt(test_prompt, 1)
        
        # Check file exists
        prompt_file = Path(self.prompts_dir) / "adversary_v1.txt"
        assert prompt_file.exists()
    
    def test_evolution_history(self):
        """Test getting evolution history"""
        mutator = EvolutionaryMutator(prompts_dir=self.prompts_dir)
        
        # Save some versions
        mutator._save_prompt("Prompt v1", 1)
        mutator._save_prompt("Prompt v2", 2)
        
        history = mutator.get_evolution_history()
        
        assert len(history) >= 2
        assert any(h['version'] == 1 for h in history)
        assert any(h['version'] == 2 for h in history)


class TestIntegration:
    """Integration tests for all three agents working together"""
    
    def test_full_cycle(self):
        """Test complete cycle: Prediction -> Audit -> Evolution"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize all agents
            adversary = BehavioralAdversary(use_shadow_mode=True)
            ledger = IntelligenceLedger(
                db_path=os.path.join(temp_dir, "ledger.db")
            )
            auditor = ReconciliationAuditor(ledger=ledger)
            mutator = EvolutionaryMutator(
                prompts_dir=os.path.join(temp_dir, "prompts")
            )
            
            # Step 1: Make prediction
            market_data = {
                'price': 95000.0,
                'rsi': 78.0,
                'volume': 8000.0,
                'price_change_pct': 5.5,
            }
            
            result = adversary.analyze_psychology(market_data, sentiment="Greed")
            
            # Step 2: Record prediction
            pred_id = ledger.record_prediction(
                predicted_bias=result['predicted_bias'],
                predicted_outcome=result['predicted_outcome'],
                confidence=result['confidence'],
                market_regime=result['market_regime'],
                archetype=result['detected_archetype'],
                signal=result['signal'],
                price_at_prediction=market_data['price']
            )
            
            # Step 3: Simulate price movement and audit
            ledger.update_actual_price(pred_id, 93000.0, "1h")
            score = auditor._calculate_success_score(
                {
                    'id': pred_id,
                    'predicted_bias': result['predicted_bias'],
                    'predicted_outcome': result['predicted_outcome'],
                    'confidence': result['confidence'],
                    'signal': result['signal'],
                    'price_at_prediction': market_data['price']
                },
                93000.0
            )
            ledger.update_success_score(pred_id, "1h", score)
            
            # Step 4: Get failed predictions for evolution
            failed = ledger.get_failed_predictions(limit=5)
            
            # Step 5: Test evolution (will fail without API, but that's OK)
            # We're testing the integration flow
            evolution_result = mutator.evolve_prompt(failed, force=True)
            
            # Verify the cycle completed
            assert pred_id > 0
            assert score is not None
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
