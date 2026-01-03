"""
Reconciliation Loop - "The Auditor" (Feedback Loop)

Mission: Create a "Memory" for the bot to judge its own intelligence.
Track every prediction, compare against actual outcomes, and maintain
an Intelligence Ledger for evolutionary learning.

Features:
- Intelligence Ledger: Persistent SQLite/JSONL database
- Prediction Tracking: timestamp, predicted_bias, outcome, confidence, regime
- Audit Logic: Runs every 1h, 4h, 12h
- Success Scoring: +1 to -1 based on prediction accuracy
- Outcome Comparison: Predicted vs Actual price action
"""
import logging
import os
import json
import sqlite3
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligenceLedger:
    """
    Persistent storage for predictions and outcomes
    
    Schema:
    - id: Integer primary key
    - timestamp: ISO timestamp
    - predicted_bias: String (e.g., "Bullish Extension", "Bearish Capitulation")
    - predicted_outcome: String (e.g., "Bull Trap / Reversal", "Mean Reversion")
    - confidence: Float (0-1)
    - market_regime: String (BULL/BEAR/CHOPPY/VOLATILE)
    - archetype: String (FOMO_CHASER, PANIC_SELLER, etc.)
    - signal: String (BUY/SELL/HOLD)
    - price_at_prediction: Float
    - actual_price_1h: Float (nullable)
    - actual_price_4h: Float (nullable)
    - actual_price_12h: Float (nullable)
    - success_score_1h: Float (nullable, -1 to +1)
    - success_score_4h: Float (nullable, -1 to +1)
    - success_score_12h: Float (nullable, -1 to +1)
    - audited: Boolean
    """
    
    def __init__(self, db_path: str = "data/intelligence_ledger.db"):
        """
        Initialize Intelligence Ledger
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        logger.info(f"IntelligenceLedger initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                predicted_bias TEXT,
                predicted_outcome TEXT,
                confidence REAL,
                market_regime TEXT,
                archetype TEXT,
                signal TEXT,
                price_at_prediction REAL,
                actual_price_1h REAL,
                actual_price_4h REAL,
                actual_price_12h REAL,
                success_score_1h REAL,
                success_score_4h REAL,
                success_score_12h REAL,
                audited INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON predictions(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audited 
            ON predictions(audited)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema initialized")
    
    def record_prediction(
        self,
        predicted_bias: str,
        predicted_outcome: str,
        confidence: float,
        market_regime: str,
        archetype: str,
        signal: str,
        price_at_prediction: float
    ) -> int:
        """
        Record a new prediction in the ledger
        
        Args:
            predicted_bias: Predicted bias (e.g., "Bullish Extension")
            predicted_outcome: Predicted outcome (e.g., "Bull Trap")
            confidence: Confidence level (0-1)
            market_regime: Market regime
            archetype: Trader archetype detected
            signal: Trading signal
            price_at_prediction: Current market price
            
        Returns:
            Prediction ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO predictions (
                timestamp, predicted_bias, predicted_outcome, confidence,
                market_regime, archetype, signal, price_at_prediction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, predicted_bias, predicted_outcome, confidence,
            market_regime, archetype, signal, price_at_prediction
        ))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded prediction #{prediction_id}: {predicted_bias} -> {predicted_outcome}")
        return prediction_id
    
    def update_actual_price(
        self,
        prediction_id: int,
        actual_price: float,
        timeframe: str
    ):
        """
        Update actual price for a prediction at specific timeframe
        
        Args:
            prediction_id: ID of the prediction
            actual_price: Actual market price at timeframe
            timeframe: Timeframe (1h, 4h, 12h)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        field_name = f"actual_price_{timeframe}"
        cursor.execute(f"""
            UPDATE predictions 
            SET {field_name} = ? 
            WHERE id = ?
        """, (actual_price, prediction_id))
        
        conn.commit()
        conn.close()
    
    def get_unaudited_predictions(
        self,
        timeframe: str,
        min_age_hours: int
    ) -> List[Dict[str, Any]]:
        """
        Get predictions that need auditing for a specific timeframe
        
        Args:
            timeframe: Timeframe to audit (1h, 4h, 12h)
            min_age_hours: Minimum age in hours (1, 4, or 12)
            
        Returns:
            List of prediction dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=min_age_hours)).isoformat()
        score_field = f"success_score_{timeframe}"
        
        cursor.execute(f"""
            SELECT * FROM predictions 
            WHERE timestamp <= ? 
            AND {score_field} IS NULL
            ORDER BY timestamp DESC
            LIMIT 100
        """, (cutoff_time,))
        
        predictions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return predictions
    
    def update_success_score(
        self,
        prediction_id: int,
        timeframe: str,
        score: float
    ):
        """
        Update success score for a prediction at specific timeframe
        
        Args:
            prediction_id: ID of the prediction
            timeframe: Timeframe (1h, 4h, 12h)
            score: Success score (-1 to +1)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        field_name = f"success_score_{timeframe}"
        cursor.execute(f"""
            UPDATE predictions 
            SET {field_name} = ? 
            WHERE id = ?
        """, (score, prediction_id))
        
        conn.commit()
        conn.close()
    
    def mark_audited(self, prediction_id: int):
        """Mark a prediction as fully audited"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE predictions 
            SET audited = 1 
            WHERE id = ?
        """, (prediction_id,))
        
        conn.commit()
        conn.close()
    
    def get_failed_predictions(
        self,
        limit: int = 5,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get top N failed predictions for evolutionary learning
        
        Args:
            limit: Number of predictions to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of failed prediction dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get predictions with negative average scores
        cursor.execute("""
            SELECT *,
                   (COALESCE(success_score_1h, 0) + 
                    COALESCE(success_score_4h, 0) + 
                    COALESCE(success_score_12h, 0)) / 3 as avg_score
            FROM predictions
            WHERE confidence >= ?
            AND (success_score_1h IS NOT NULL OR 
                 success_score_4h IS NOT NULL OR 
                 success_score_12h IS NOT NULL)
            ORDER BY avg_score ASC
            LIMIT ?
        """, (min_confidence, limit))
        
        predictions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return predictions
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall ledger statistics
        
        Returns:
            Statistics dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total = cursor.fetchone()[0]
        
        # Audited predictions
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE audited = 1")
        audited = cursor.fetchone()[0]
        
        # Average scores
        cursor.execute("""
            SELECT 
                AVG(success_score_1h) as avg_1h,
                AVG(success_score_4h) as avg_4h,
                AVG(success_score_12h) as avg_12h
            FROM predictions
            WHERE success_score_1h IS NOT NULL
        """)
        scores = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_predictions": total,
            "audited_predictions": audited,
            "pending_audit": total - audited,
            "avg_score_1h": scores[0] if scores[0] else 0.0,
            "avg_score_4h": scores[1] if scores[1] else 0.0,
            "avg_score_12h": scores[2] if scores[2] else 0.0
        }


class ReconciliationAuditor:
    """
    The Auditor - Reconciliation Loop for prediction validation
    
    Runs audits at 1h, 4h, and 12h intervals to compare predictions
    against actual market outcomes and assign success scores.
    """
    
    def __init__(
        self,
        ledger: Optional[IntelligenceLedger] = None,
        price_fetcher: Optional[callable] = None
    ):
        """
        Initialize Reconciliation Auditor
        
        Args:
            ledger: IntelligenceLedger instance (creates new if None)
            price_fetcher: Function to fetch current market price
        """
        self.ledger = ledger or IntelligenceLedger()
        self.price_fetcher = price_fetcher
        
        # Audit intervals (hours)
        self.audit_intervals = [1, 4, 12]
        
        # Last audit times
        self.last_audit_times = {
            "1h": None,
            "4h": None,
            "12h": None
        }
        
        logger.info("ReconciliationAuditor initialized")
    
    def run_audit_cycle(self, current_price: Optional[float] = None):
        """
        Run a complete audit cycle for all timeframes
        
        Args:
            current_price: Current market price (fetch if not provided)
        """
        logger.info("="*60)
        logger.info("RECONCILIATION AUDIT CYCLE")
        logger.info("="*60)
        
        # Get current price
        if current_price is None and self.price_fetcher:
            try:
                current_price = self.price_fetcher()
            except Exception as e:
                logger.error(f"Failed to fetch price: {str(e)}")
                return
        
        if current_price is None:
            logger.warning("No current price available, skipping audit")
            return
        
        # Run audits for each timeframe
        for interval in self.audit_intervals:
            timeframe = f"{interval}h"
            logger.info(f"\n🔍 Auditing {timeframe} predictions...")
            
            self._audit_timeframe(timeframe, interval, current_price)
            self.last_audit_times[timeframe] = datetime.now()
        
        # Display statistics
        stats = self.ledger.get_statistics()
        logger.info("\n📊 AUDIT STATISTICS")
        logger.info(f"Total Predictions: {stats['total_predictions']}")
        logger.info(f"Audited: {stats['audited_predictions']}")
        logger.info(f"Pending Audit: {stats['pending_audit']}")
        logger.info(f"Avg Score 1h: {stats['avg_score_1h']:.2f}")
        logger.info(f"Avg Score 4h: {stats['avg_score_4h']:.2f}")
        logger.info(f"Avg Score 12h: {stats['avg_score_12h']:.2f}")
    
    def _audit_timeframe(
        self,
        timeframe: str,
        hours: int,
        current_price: float
    ):
        """
        Audit predictions for a specific timeframe
        
        Args:
            timeframe: Timeframe string (1h, 4h, 12h)
            hours: Hours since prediction
            current_price: Current market price
        """
        # Get unaudited predictions
        predictions = self.ledger.get_unaudited_predictions(timeframe, hours)
        
        logger.info(f"Found {len(predictions)} predictions to audit for {timeframe}")
        
        for pred in predictions:
            # Update actual price
            self.ledger.update_actual_price(pred['id'], current_price, timeframe)
            
            # Calculate success score
            score = self._calculate_success_score(pred, current_price)
            
            # Update success score
            self.ledger.update_success_score(pred['id'], timeframe, score)
            
            # Check if fully audited (all timeframes complete)
            if self._is_fully_audited(pred['id']):
                self.ledger.mark_audited(pred['id'])
            
            logger.debug(f"Prediction #{pred['id']}: {pred['predicted_bias']} -> Score: {score:.2f}")
    
    def _calculate_success_score(
        self,
        prediction: Dict[str, Any],
        actual_price: float
    ) -> float:
        """
        Calculate success score for a prediction
        
        Score Logic:
        - If predicted Bull Trap and price went down: +1
        - If predicted Mean Reversion and price went up: +1
        - If predicted opposite to actual outcome: -1
        - Partial credit for direction accuracy: 0 to +/-1
        
        Args:
            prediction: Prediction dict
            actual_price: Actual price at timeframe
            
        Returns:
            Success score (-1 to +1)
        """
        predicted_price = prediction['price_at_prediction']
        predicted_outcome = prediction['predicted_outcome'] or ""
        signal = prediction['signal']
        confidence = prediction['confidence']
        
        # Calculate price change
        price_change_pct = ((actual_price - predicted_price) / predicted_price) * 100
        
        # Determine if prediction was correct
        score = 0.0
        
        # Check signal accuracy
        if signal == 'BUY':
            # Predicted upward movement
            if price_change_pct > 0:
                score = min(price_change_pct / 5.0, 1.0)  # Scale to +1
            else:
                score = max(price_change_pct / 5.0, -1.0)  # Scale to -1
        
        elif signal == 'SELL':
            # Predicted downward movement
            if price_change_pct < 0:
                score = min(abs(price_change_pct) / 5.0, 1.0)  # Scale to +1
            else:
                score = max(-price_change_pct / 5.0, -1.0)  # Scale to -1
        
        # Check outcome accuracy for specific patterns
        if "reversal" in predicted_outcome.lower() or "trap" in predicted_outcome.lower():
            # Predicted reversal/trap - check if it happened
            if signal == 'SELL' and price_change_pct < -1:
                score = max(score, 0.8)  # Strong confirmation
            elif signal == 'BUY' and price_change_pct > 1:
                score = max(score, 0.8)
        
        elif "mean reversion" in predicted_outcome.lower():
            # Predicted mean reversion
            if signal == 'BUY' and price_change_pct > 0:
                score = max(score, 0.7)
            elif signal == 'SELL' and price_change_pct < 0:
                score = max(score, 0.7)
        
        # Weight by confidence
        score *= confidence
        
        return round(score, 3)
    
    def _is_fully_audited(self, prediction_id: int) -> bool:
        """
        Check if prediction has been audited for all timeframes
        
        Args:
            prediction_id: Prediction ID
            
        Returns:
            True if fully audited
        """
        conn = sqlite3.connect(self.ledger.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT success_score_1h, success_score_4h, success_score_12h
            FROM predictions
            WHERE id = ?
        """, (prediction_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
        
        # Check if all scores are not None
        return all(score is not None for score in result)
    
    def get_failed_predictions_for_learning(
        self,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top N failed predictions for evolutionary mutator
        
        Args:
            top_n: Number of predictions to return
            
        Returns:
            List of failed prediction dicts
        """
        return self.ledger.get_failed_predictions(limit=top_n)


def test_reconciliation_auditor():
    """
    Validation tests for Reconciliation Auditor
    """
    logger.info("="*60)
    logger.info("RECONCILIATION AUDITOR - VALIDATION TESTS")
    logger.info("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Use in-memory database for testing
    import tempfile
    temp_dir = tempfile.mkdtemp()
    test_db = os.path.join(temp_dir, "test_ledger.db")
    
    # Test 1: Record and Retrieve Prediction
    logger.info("\n📝 Test 1: Record and Retrieve Prediction")
    try:
        ledger = IntelligenceLedger(db_path=test_db)
        
        pred_id = ledger.record_prediction(
            predicted_bias="Bullish Extension",
            predicted_outcome="Bull Trap / Reversal",
            confidence=0.8,
            market_regime="BULL",
            archetype="FOMO_CHASER",
            signal="SELL",
            price_at_prediction=95000.0
        )
        
        if pred_id > 0:
            logger.info(f"✅ Test 1 PASSED: Recorded prediction #{pred_id}")
            tests_passed += 1
        else:
            logger.error("❌ Test 1 FAILED: Could not record prediction")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED with exception: {str(e)}")
        tests_failed += 1
    
    # Test 2: Audit Success Score (False Positive Detection)
    logger.info("\n🔍 Test 2: Audit Test - False Positive Detection")
    try:
        auditor = ReconciliationAuditor(ledger=ledger)
        
        # Record prediction that will be wrong
        pred_id = ledger.record_prediction(
            predicted_bias="Bearish Capitulation",
            predicted_outcome="Mean Reversion",
            confidence=0.9,
            market_regime="BEAR",
            archetype="PANIC_SELLER",
            signal="BUY",
            price_at_prediction=85000.0
        )
        
        # Simulate price going DOWN (opposite of prediction)
        actual_price = 82000.0  # -3.5% instead of mean reversion up
        
        # Manually calculate score to test
        prediction = {
            'id': pred_id,
            'predicted_bias': 'Bearish Capitulation',
            'predicted_outcome': 'Mean Reversion',
            'confidence': 0.9,
            'signal': 'BUY',
            'price_at_prediction': 85000.0
        }
        
        score = auditor._calculate_success_score(prediction, actual_price)
        
        # Should be negative score (false positive)
        if score < 0:
            logger.info(f"✅ Test 2 PASSED: False Positive detected, score: {score:.2f}")
            tests_passed += 1
        else:
            logger.error(f"❌ Test 2 FAILED: Expected negative score, got {score:.2f}")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Test 2 FAILED with exception: {str(e)}")
        tests_failed += 1
    
    # Test 3: Get Failed Predictions
    logger.info("\n❌ Test 3: Get Failed Predictions for Learning")
    try:
        # Record a few more predictions with varying outcomes
        for i in range(3):
            pred_id = ledger.record_prediction(
                predicted_bias=f"Test Bias {i}",
                predicted_outcome=f"Test Outcome {i}",
                confidence=0.7,
                market_regime="CHOPPY",
                archetype="NEUTRAL",
                signal="HOLD",
                price_at_prediction=90000.0
            )
            
            # Set some negative scores
            ledger.update_success_score(pred_id, "1h", -0.5 - i*0.1)
        
        failed = ledger.get_failed_predictions(limit=5)
        
        if len(failed) > 0:
            logger.info(f"✅ Test 3 PASSED: Retrieved {len(failed)} failed predictions")
            tests_passed += 1
        else:
            logger.error("❌ Test 3 FAILED: No failed predictions found")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Test 3 FAILED with exception: {str(e)}")
        tests_failed += 1
    
    # Test 4: Statistics
    logger.info("\n📊 Test 4: Ledger Statistics")
    try:
        stats = ledger.get_statistics()
        
        if stats['total_predictions'] > 0:
            logger.info(f"✅ Test 4 PASSED: Statistics retrieved")
            logger.info(f"   Total: {stats['total_predictions']}, Audited: {stats['audited_predictions']}")
            tests_passed += 1
        else:
            logger.error("❌ Test 4 FAILED: No statistics found")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Test 4 FAILED with exception: {str(e)}")
        tests_failed += 1
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"✅ Tests Passed: {tests_passed}")
    logger.info(f"❌ Tests Failed: {tests_failed}")
    
    if tests_failed == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        return True
    else:
        logger.warning(f"⚠️  {tests_failed} test(s) failed")
        return False


if __name__ == "__main__":
    # Run tests when executed directly
    success = test_reconciliation_auditor()
    exit(0 if success else 1)
