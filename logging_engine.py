"""
WEEX AI Log Engine - Competition Submission Requirement

This module generates AI logs that prove LLM decision-making for tournament submission.
Each trade must have a corresponding JSON log with:
- Timestamp
- Model version
- Input data (RSI, funding rate, sentiment, etc.)
- AI reasoning
- Order details

Logs are stored in ai_logs/ directory with ISO timestamp filenames.
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AILogEngine:
    """
    AI Log Engine for WEEX Tournament Compliance
    
    Generates JSON logs that prove AI/LLM decision-making for every trade.
    Required for tournament submission and ranking eligibility.
    """
    
    def __init__(self, log_dir: str = "ai_logs"):
        """
        Initialize AI Log Engine
        
        Args:
            log_dir: Directory to store AI logs (default: ai_logs)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"✅ AI Log Engine initialized: {self.log_dir}")
    
    def generate_trade_log(
        self,
        symbol: str,
        side: str,
        size: str,
        leverage: str,
        model_version: str,
        ai_reasoning: str,
        inputs: Dict[str, Any],
        trade_id: Optional[str] = None
    ) -> str:
        """
        Generate AI log for a single trade
        
        Args:
            symbol: Trading symbol (e.g., "cmt_btcusdt")
            side: Order side ("buy" or "sell")
            size: Position size
            leverage: Leverage used
            model_version: AI model version (e.g., "GPT-4o-Competition-V1")
            ai_reasoning: AI's reasoning for the trade decision
            inputs: Model inputs (RSI, funding_rate, sentiment_score, etc.)
            trade_id: Optional trade identifier
            
        Returns:
            Path to the generated log file
        """
        try:
            # Generate timestamp
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            # Build log structure
            log_data = {
                "timestamp": timestamp,
                "model_version": model_version,
                "inputs": inputs,
                "ai_reasoning": ai_reasoning,
                "order_details": {
                    "symbol": symbol,
                    "side": side.lower(),
                    "size": size,
                    "leverage": leverage
                }
            }
            
            # Add trade_id if provided
            if trade_id:
                log_data["trade_id"] = trade_id
            
            # Generate filename with timestamp (sanitized for filesystem compatibility)
            # Remove or replace characters that may cause issues on different filesystems
            safe_timestamp = timestamp.replace(':', '-').replace('.', '_')
            # Additional sanitization to ensure cross-platform compatibility
            safe_timestamp = ''.join(c if c.isalnum() or c in '-_' else '_' for c in safe_timestamp)
            filename = f"trade_{safe_timestamp}.json"
            filepath = self.log_dir / filename
            
            # Write log file
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"📝 AI log generated: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate AI log: {str(e)}")
            return ""
    
    def generate_decision_log(
        self,
        symbol: str,
        decision: str,
        confidence: float,
        model_version: str,
        ai_reasoning: str,
        inputs: Dict[str, Any]
    ) -> str:
        """
        Generate AI log for a trading decision (including HOLD)
        
        Args:
            symbol: Trading symbol
            decision: Decision made ("BUY", "SELL", or "HOLD")
            confidence: Confidence score (0-1)
            model_version: AI model version
            ai_reasoning: AI's reasoning for the decision
            inputs: Model inputs
            
        Returns:
            Path to the generated log file
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            log_data = {
                "timestamp": timestamp,
                "model_version": model_version,
                "decision": decision,
                "confidence": confidence,
                "inputs": inputs,
                "ai_reasoning": ai_reasoning,
                "symbol": symbol
            }
            
            # Generate filename with sanitized timestamp
            safe_timestamp = timestamp.replace(':', '-').replace('.', '_')
            safe_timestamp = ''.join(c if c.isalnum() or c in '-_' else '_' for c in safe_timestamp)
            filename = f"decision_{safe_timestamp}.json"
            filepath = self.log_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.debug(f"📝 AI decision log generated: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate AI decision log: {str(e)}")
            return ""
    
    def get_log_count(self) -> int:
        """
        Get total number of AI logs generated
        
        Returns:
            Number of log files in the log directory
        """
        try:
            log_files = list(self.log_dir.glob("*.json"))
            return len(log_files)
        except Exception as e:
            logger.error(f"Failed to count logs: {str(e)}")
            return 0
    
    def get_trade_log_count(self) -> int:
        """
        Get number of trade logs (excludes decision logs)
        
        Returns:
            Number of trade log files
        """
        try:
            trade_logs = list(self.log_dir.glob("trade_*.json"))
            return len(trade_logs)
        except Exception as e:
            logger.error(f"Failed to count trade logs: {str(e)}")
            return 0
    
    def cleanup_old_logs(self, max_logs: int = 10000) -> None:
        """
        Clean up old logs if count exceeds max_logs
        Keeps the most recent logs
        
        Args:
            max_logs: Maximum number of logs to keep
        """
        try:
            log_files = sorted(self.log_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
            
            if len(log_files) > max_logs:
                files_to_delete = log_files[:-max_logs]
                for file in files_to_delete:
                    file.unlink()
                logger.info(f"🧹 Cleaned up {len(files_to_delete)} old log files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup logs: {str(e)}")
