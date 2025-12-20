"""
Guardrails - Safety mechanisms for the self-evolving system
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import ast
import sys
from io import StringIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Guardrails:
    """
    Safety guardrails for the Aether-Evo system
    - 12h stability lock after logic evolution
    - 3% 1h equity kill-switch
    - Syntax and logic audit before code rewrite
    """
    
    def __init__(self, initial_equity: float, kill_switch_threshold: float, stability_lock_hours: int):
        """Initialize guardrails"""
        self.initial_equity = initial_equity
        self.current_equity = initial_equity
        self.kill_switch_threshold = kill_switch_threshold
        self.stability_lock_hours = stability_lock_hours
        
        self.last_evolution_time: Optional[datetime] = None
        self.equity_history: list = []
        self.kill_switch_triggered = False
        
    def update_equity(self, new_equity: float):
        """Update current equity and check kill-switch"""
        self.current_equity = new_equity
        self.equity_history.append({
            'timestamp': datetime.now(),
            'equity': new_equity
        })
        
        # Check 1-hour kill-switch
        self._check_kill_switch()
    
    def _check_kill_switch(self):
        """Check if 1-hour equity drop exceeds threshold"""
        if self.kill_switch_triggered:
            return
        
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Get equity from 1 hour ago
        recent_history = [
            h for h in self.equity_history 
            if h['timestamp'] >= one_hour_ago
        ]
        
        if not recent_history:
            return
        
        equity_1h_ago = recent_history[0]['equity']
        equity_change = (self.current_equity - equity_1h_ago) / equity_1h_ago
        
        if equity_change <= -self.kill_switch_threshold:
            self.kill_switch_triggered = True
            logger.critical(
                f"KILL SWITCH TRIGGERED! Equity dropped {abs(equity_change):.2%} in 1 hour "
                f"(threshold: {self.kill_switch_threshold:.2%})"
            )
    
    def is_kill_switch_active(self) -> bool:
        """Check if kill-switch is active"""
        return self.kill_switch_triggered
    
    def can_evolve(self) -> bool:
        """Check if system can evolve (12h stability lock)"""
        if self.last_evolution_time is None:
            return True
        
        time_since_evolution = datetime.now() - self.last_evolution_time
        hours_since = time_since_evolution.total_seconds() / 3600
        
        if hours_since < self.stability_lock_hours:
            logger.info(
                f"Evolution locked: {hours_since:.1f}h since last evolution "
                f"(lock: {self.stability_lock_hours}h)"
            )
            return False
        
        return True
    
    def validate_code_syntax(self, code: str) -> tuple[bool, str]:
        """
        Validate Python code syntax
        
        Returns:
            (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            logger.error(f"Code validation failed: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Code validation failed: {error_msg}")
            return False, error_msg
    
    def validate_code_logic(self, code: str) -> tuple[bool, str]:
        """
        Validate code logic and required functions
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Required functions
            required_functions = ['calculate_indicators', 'generate_signal']
            found_functions = []
            
            # Find all function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    found_functions.append(node.name)
            
            # Check if required functions exist
            missing_functions = [f for f in required_functions if f not in found_functions]
            
            if missing_functions:
                error_msg = f"Missing required functions: {', '.join(missing_functions)}"
                logger.error(f"Logic validation failed: {error_msg}")
                return False, error_msg
            
            # Try to import the code (dry run)
            test_globals = {}
            exec(code, test_globals)
            
            # Verify functions are callable
            for func_name in required_functions:
                if not callable(test_globals.get(func_name)):
                    error_msg = f"Function {func_name} is not callable"
                    logger.error(f"Logic validation failed: {error_msg}")
                    return False, error_msg
            
            logger.info("Code logic validation passed")
            return True, ""
            
        except Exception as e:
            error_msg = f"Logic validation error: {str(e)}"
            logger.error(f"Logic validation failed: {error_msg}")
            return False, error_msg
    
    def audit_code(self, code: str) -> tuple[bool, str]:
        """
        Complete audit: syntax + logic validation
        
        Returns:
            (is_valid, error_message)
        """
        logger.info("Starting code audit...")
        
        # Syntax validation
        syntax_valid, syntax_error = self.validate_code_syntax(code)
        if not syntax_valid:
            return False, f"Syntax audit failed: {syntax_error}"
        
        # Logic validation
        logic_valid, logic_error = self.validate_code_logic(code)
        if not logic_valid:
            return False, f"Logic audit failed: {logic_error}"
        
        logger.info("Code audit passed successfully")
        return True, ""
    
    def mark_evolution(self):
        """Mark that evolution occurred (start stability lock)"""
        self.last_evolution_time = datetime.now()
        logger.info(f"Evolution marked at {self.last_evolution_time.isoformat()}")
        logger.info(f"Stability lock active for {self.stability_lock_hours} hours")
    
    def get_status(self) -> Dict[str, Any]:
        """Get guardrails status"""
        can_evolve = self.can_evolve()
        
        status = {
            'kill_switch_active': self.kill_switch_triggered,
            'current_equity': self.current_equity,
            'initial_equity': self.initial_equity,
            'equity_change_pct': ((self.current_equity - self.initial_equity) / self.initial_equity) * 100,
            'can_evolve': can_evolve,
            'last_evolution': self.last_evolution_time.isoformat() if self.last_evolution_time else None,
        }
        
        if self.last_evolution_time:
            hours_since = (datetime.now() - self.last_evolution_time).total_seconds() / 3600
            status['hours_since_evolution'] = hours_since
            status['stability_lock_remaining'] = max(0, self.stability_lock_hours - hours_since)
        
        return status
