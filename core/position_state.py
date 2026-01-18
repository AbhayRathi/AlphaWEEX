"""
Position State Persistence - Save/restore active position state for bot resumption.

Provides JSON-based persistence for active trading positions so the bot can
resume managing TPs/SLs after restart without losing state.
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class PositionStatePersistence:
    """
    JSON-based position state persistence.
    
    Features:
    - Save position_scaling_state to disk
    - Restore position_scaling_state on startup
    - Thread-safe operations
    - Automatic file creation
    """
    
    def __init__(self, state_path: str = "data/active_positions.json"):
        """
        Initialize Position State Persistence
        
        Args:
            state_path: Path to the JSON state file
        """
        self.state_path = state_path
        self.lock = Lock()
        self._ensure_state_file_exists()
        logger.info(f"✅ PositionStatePersistence initialized: {self.state_path}")
    
    def _ensure_state_file_exists(self) -> None:
        """Create state file and directory if they don't exist"""
        try:
            # Create directory if needed
            state_dir = os.path.dirname(self.state_path)
            if state_dir:
                os.makedirs(state_dir, exist_ok=True)
            
            # Create empty state file if it doesn't exist
            if not os.path.exists(self.state_path):
                with open(self.state_path, 'w') as f:
                    json.dump({}, f)
                logger.info(f"📝 Created new position state file: {self.state_path}")
        except Exception as e:
            logger.error(f"Failed to create state file: {str(e)}")
            raise
    
    def save_state(self, position_scaling_state: Dict[str, Dict[str, Any]]) -> bool:
        """
        Save position scaling state to disk
        
        Args:
            position_scaling_state: Dictionary of position states by symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.lock:
                with open(self.state_path, 'w') as f:
                    json.dump(position_scaling_state, f, indent=2)
            
            logger.debug(f"💾 Position state saved: {len(position_scaling_state)} positions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save position state: {str(e)}")
            return False
    
    def load_state(self) -> Dict[str, Dict[str, Any]]:
        """
        Load position scaling state from disk
        
        Returns:
            Dictionary of position states by symbol (empty dict if file doesn't exist or is invalid)
        """
        try:
            with self.lock:
                if not os.path.exists(self.state_path):
                    logger.info("No existing position state file found, starting fresh")
                    return {}
                
                with open(self.state_path, 'r') as f:
                    state = json.load(f)
                
                if not isinstance(state, dict):
                    logger.warning("Invalid position state format, starting fresh")
                    return {}
                
                logger.info(f"📂 Position state loaded: {len(state)} positions")
                return state
                
        except json.JSONDecodeError:
            logger.warning("Corrupted position state file, starting fresh")
            return {}
        except Exception as e:
            logger.error(f"Failed to load position state: {str(e)}")
            return {}
    
    def clear_state(self) -> bool:
        """
        Clear all position state (use when all positions are closed)
        
        Returns:
            True if successful
        """
        try:
            with self.lock:
                with open(self.state_path, 'w') as f:
                    json.dump({}, f)
            logger.info("🗑️ Position state cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear position state: {str(e)}")
            return False
