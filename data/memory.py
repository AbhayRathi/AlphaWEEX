"""
Evolution Memory Management
Tracks performance history and manages parameter blacklisting
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvolutionMemory:
    """
    Manages evolution history and self-correction memory
    
    Features:
    - Track evolution history with timestamps
    - Monitor PnL over 2-hour windows
    - Blacklist parameters that result in negative PnL
    - Persist memory to JSON file
    """
    
    def __init__(self, history_file: str = "data/evolution_history.json"):
        """
        Initialize Evolution Memory
        
        Args:
            history_file: Path to evolution history JSON file
        """
        self.history_file = Path(history_file)
        self.data = self._load_history()
        
    def _load_history(self) -> Dict[str, Any]:
        """Load evolution history from JSON file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded evolution history: {len(data.get('evolutions', []))} evolutions")
                    return data
            except Exception as e:
                logger.error(f"Error loading evolution history: {str(e)}")
                return self._default_structure()
        else:
            logger.info("No evolution history found, creating new")
            return self._default_structure()
    
    def _default_structure(self) -> Dict[str, Any]:
        """Get default evolution history structure"""
        return {
            "evolutions": [],
            "blacklisted_parameters": [],
            "performance_windows": []
        }
    
    def _save_history(self):
        """Save evolution history to JSON file"""
        try:
            # Create directory if it doesn't exist
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info("Evolution history saved")
        except Exception as e:
            logger.error(f"Error saving evolution history: {str(e)}")
    
    def record_evolution(
        self,
        parameters: Dict[str, Any],
        reason: str,
        suggestion: str,
        initial_equity: float
    ):
        """
        Record a new evolution event
        
        Args:
            parameters: Parameters used in this evolution
            reason: Reason for evolution
            suggestion: Suggested improvements
            initial_equity: Equity at the time of evolution
        """
        evolution_record = {
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters,
            "reason": reason,
            "suggestion": suggestion,
            "initial_equity": initial_equity,
            "start_time": datetime.now().isoformat()
        }
        
        self.data["evolutions"].append(evolution_record)
        self._save_history()
        
        logger.info(f"Recorded evolution: {reason}")
    
    def update_performance_window(
        self,
        evolution_index: int,
        current_equity: float,
        pnl: float
    ):
        """
        Update performance for a 2-hour window after evolution
        
        Args:
            evolution_index: Index of the evolution in the history
            current_equity: Current equity
            pnl: Profit/Loss since evolution
        """
        if evolution_index >= len(self.data["evolutions"]):
            logger.warning(f"Invalid evolution index: {evolution_index}")
            return
        
        evolution = self.data["evolutions"][evolution_index]
        evolution_time = datetime.fromisoformat(evolution["start_time"])
        current_time = datetime.now()
        
        # Check if we're within 2-hour window
        time_elapsed = current_time - evolution_time
        if time_elapsed > timedelta(hours=2):
            # Window closed - check if PnL is negative
            if pnl < 0:
                self._blacklist_parameters(evolution["parameters"], pnl, evolution_index)
            
            # Mark as evaluated
            evolution["evaluated"] = True
            evolution["final_pnl"] = pnl
            evolution["final_equity"] = current_equity
            self._save_history()
            
            logger.info(
                f"Evolution {evolution_index} window closed: "
                f"PnL={pnl:.2f}, Blacklisted={pnl < 0}"
            )
        else:
            # Still within window, update current performance
            evolution["current_equity"] = current_equity
            evolution["current_pnl"] = pnl
            evolution["last_update"] = current_time.isoformat()
            self._save_history()
    
    def _blacklist_parameters(self, parameters: Dict[str, Any], pnl: float, evolution_index: int):
        """
        Blacklist parameters that resulted in negative PnL
        
        Args:
            parameters: Parameters to blacklist
            pnl: Negative PnL that triggered blacklisting
            evolution_index: Index of the failed evolution
        """
        blacklist_entry = {
            "parameters": parameters,
            "pnl": pnl,
            "timestamp": datetime.now().isoformat(),
            "evolution_index": evolution_index,
            "reason": f"Negative PnL ({pnl:.2f}) over 2-hour window"
        }
        
        self.data["blacklisted_parameters"].append(blacklist_entry)
        self._save_history()
        
        logger.warning(
            f"⚠️  Parameters blacklisted due to negative PnL: {pnl:.2f}\n"
            f"   Parameters: {parameters}"
        )
    
    def is_blacklisted(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Check if parameters are blacklisted
        
        Args:
            parameters: Parameters to check
            
        Returns:
            (is_blacklisted, reason)
        """
        for entry in self.data["blacklisted_parameters"]:
            # Check if parameters match (simplified - can be made more sophisticated)
            if self._parameters_match(entry["parameters"], parameters):
                reason = entry.get("reason", "Unknown reason")
                return True, reason
        
        return False, None
    
    def _parameters_match(self, blacklisted: Dict[str, Any], proposed: Dict[str, Any]) -> bool:
        """
        Check if proposed parameters match blacklisted ones
        
        Args:
            blacklisted: Blacklisted parameters
            proposed: Proposed parameters
            
        Returns:
            True if they match (within tolerance)
        """
        # Simple exact match for now
        # In production, you might want fuzzy matching or key parameter comparison
        return blacklisted == proposed
    
    def get_recent_evolutions(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get most recent evolutions
        
        Args:
            count: Number of recent evolutions to retrieve
            
        Returns:
            List of recent evolution records
        """
        evolutions = self.data.get("evolutions", [])
        return evolutions[-count:] if evolutions else []
    
    def get_blacklisted_count(self) -> int:
        """Get count of blacklisted parameter sets"""
        return len(self.data.get("blacklisted_parameters", []))
    
    def get_evolution_count(self) -> int:
        """Get total count of evolutions"""
        return len(self.data.get("evolutions", []))
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get evolution memory statistics
        
        Returns:
            Dictionary with statistics
        """
        evolutions = self.data.get("evolutions", [])
        blacklisted = self.data.get("blacklisted_parameters", [])
        
        # Calculate success rate
        evaluated = [e for e in evolutions if e.get("evaluated", False)]
        failed = len(blacklisted)
        success_rate = ((len(evaluated) - failed) / len(evaluated) * 100) if evaluated else 0
        
        return {
            "total_evolutions": len(evolutions),
            "evaluated_evolutions": len(evaluated),
            "blacklisted_parameters": len(blacklisted),
            "success_rate": success_rate,
            "pending_evaluations": len([e for e in evolutions if not e.get("evaluated", False)])
        }
    
    def clear_old_blacklist(self, days: int = 30):
        """
        Clear blacklist entries older than specified days
        
        Args:
            days: Number of days after which to clear blacklist entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        original_count = len(self.data["blacklisted_parameters"])
        self.data["blacklisted_parameters"] = [
            entry for entry in self.data["blacklisted_parameters"]
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]
        
        removed = original_count - len(self.data["blacklisted_parameters"])
        if removed > 0:
            self._save_history()
            logger.info(f"Cleared {removed} old blacklist entries (older than {days} days)")
