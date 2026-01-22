"""
Tests for AILogEngine - Tournament Compliance
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_engine import AILogEngine


class TestAILogEngine(unittest.TestCase):
    """Test cases for AILogEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()
        self.log_engine = AILogEngine(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_init_creates_directory(self):
        """Test that initialization creates the log directory"""
        self.assertTrue(Path(self.test_dir).exists())
        self.assertTrue(Path(self.test_dir).is_dir())
    
    def test_generate_trade_log(self):
        """Test generating a trade log"""
        log_path = self.log_engine.generate_trade_log(
            symbol="cmt_btcusdt",
            side="buy",
            size="0.001",
            leverage="20",
            model_version="GPT-4o-Competition-V1",
            ai_reasoning="RSI oversold on 15m chart with positive news sentiment. Executing Long.",
            inputs={
                "rsi": 32.5,
                "funding_rate": 0.01,
                "sentiment_score": 0.85
            },
            trade_id="test123"
        )
        
        # Verify log file was created
        self.assertTrue(os.path.exists(log_path))
        
        # Verify log content
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["model_version"], "GPT-4o-Competition-V1")
        self.assertEqual(log_data["order_details"]["symbol"], "cmt_btcusdt")
        self.assertEqual(log_data["order_details"]["side"], "buy")
        self.assertEqual(log_data["order_details"]["size"], "0.001")
        self.assertEqual(log_data["order_details"]["leverage"], "20")
        self.assertEqual(log_data["ai_reasoning"], "RSI oversold on 15m chart with positive news sentiment. Executing Long.")
        self.assertEqual(log_data["inputs"]["rsi"], 32.5)
        self.assertEqual(log_data["inputs"]["funding_rate"], 0.01)
        self.assertEqual(log_data["inputs"]["sentiment_score"], 0.85)
        self.assertEqual(log_data["trade_id"], "test123")
        self.assertIn("timestamp", log_data)
    
    def test_generate_decision_log(self):
        """Test generating a decision log"""
        log_path = self.log_engine.generate_decision_log(
            symbol="cmt_ethusdt",
            decision="HOLD",
            confidence=0.45,
            model_version="GPT-4o-Competition-V1",
            ai_reasoning="Neutral market conditions, insufficient confidence to trade",
            inputs={
                "rsi": 52.0,
                "sma_20": 2500.0
            }
        )
        
        # Verify log file was created
        self.assertTrue(os.path.exists(log_path))
        
        # Verify log content
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        self.assertEqual(log_data["decision"], "HOLD")
        self.assertEqual(log_data["confidence"], 0.45)
        self.assertEqual(log_data["symbol"], "cmt_ethusdt")
        self.assertIn("timestamp", log_data)
    
    def test_get_log_count(self):
        """Test getting log count"""
        # Generate multiple logs
        for i in range(5):
            self.log_engine.generate_trade_log(
                symbol="cmt_btcusdt",
                side="buy",
                size="0.001",
                leverage="20",
                model_version="Test-V1",
                ai_reasoning=f"Test log {i}",
                inputs={"test": i}
            )
        
        count = self.log_engine.get_log_count()
        self.assertEqual(count, 5)
    
    def test_get_trade_log_count(self):
        """Test getting trade log count (excludes decision logs)"""
        # Generate trade logs
        for i in range(3):
            self.log_engine.generate_trade_log(
                symbol="cmt_btcusdt",
                side="buy",
                size="0.001",
                leverage="20",
                model_version="Test-V1",
                ai_reasoning=f"Trade log {i}",
                inputs={"test": i}
            )
        
        # Generate decision logs
        for i in range(2):
            self.log_engine.generate_decision_log(
                symbol="cmt_btcusdt",
                decision="HOLD",
                confidence=0.5,
                model_version="Test-V1",
                ai_reasoning=f"Decision log {i}",
                inputs={"test": i}
            )
        
        trade_count = self.log_engine.get_trade_log_count()
        total_count = self.log_engine.get_log_count()
        
        self.assertEqual(trade_count, 3)
        self.assertEqual(total_count, 5)
    
    def test_cleanup_old_logs(self):
        """Test cleaning up old logs"""
        # Generate 15 logs
        for i in range(15):
            self.log_engine.generate_trade_log(
                symbol="cmt_btcusdt",
                side="buy",
                size="0.001",
                leverage="20",
                model_version="Test-V1",
                ai_reasoning=f"Test log {i}",
                inputs={"test": i}
            )
        
        # Clean up, keeping only 10
        self.log_engine.cleanup_old_logs(max_logs=10)
        
        count = self.log_engine.get_log_count()
        self.assertEqual(count, 10)
    
    def test_log_format_compliance(self):
        """Test that logs meet WEEX tournament format requirements"""
        log_path = self.log_engine.generate_trade_log(
            symbol="cmt_btcusdt",
            side="buy",
            size="0.001",
            leverage="20",
            model_version="GPT-4o-Competition-V1",
            ai_reasoning="Buy signal",
            inputs={"rsi": 30.0}
        )
        
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        # Verify required fields exist
        required_fields = ["timestamp", "model_version", "inputs", "ai_reasoning", "order_details"]
        for field in required_fields:
            self.assertIn(field, log_data, f"Missing required field: {field}")
        
        # Verify order_details structure
        order_required = ["symbol", "side", "size", "leverage"]
        for field in order_required:
            self.assertIn(field, log_data["order_details"], f"Missing order_details field: {field}")
        
        # Verify timestamp format (ISO 8601)
        self.assertTrue(log_data["timestamp"].endswith("Z"))
        self.assertIn("T", log_data["timestamp"])


if __name__ == '__main__':
    unittest.main()
