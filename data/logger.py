"""
Telemetry Logger for AlphaWEEX Phase 3
Logs reasoning traces from DeepSeek-R1 for analysis and debugging
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReasoningLogger:
    """
    Telemetry Logger for R1 Reasoning Traces
    
    Features:
    - Logs every DeepSeek-R1 reasoning trace
    - Extracts <thought> tags from responses
    - Saves to JSONL format for easy analysis
    - Supports log rotation and management
    """
    
    def __init__(self, log_file: str = "data/reasoning_logs.jsonl", max_size_mb: int = 100):
        """
        Initialize Reasoning Logger
        
        Args:
            log_file: Path to JSONL log file
            max_size_mb: Maximum log file size in MB before rotation
        """
        self.log_file = Path(log_file)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Create directory if needed
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.touch()
            logger.info(f"Created reasoning log file: {self.log_file}")
    
    def extract_thought_tags(self, text: str) -> list:
        """
        Extract <thought> tags from DeepSeek-R1 response
        
        Args:
            text: Response text that may contain <thought> tags
            
        Returns:
            List of thought contents
        """
        # Pattern to match <thought>...</thought> tags
        pattern = r'<thought>(.*?)</thought>'
        thoughts = re.findall(pattern, text, re.DOTALL)
        
        # Clean up thoughts (strip whitespace)
        cleaned_thoughts = [thought.strip() for thought in thoughts]
        
        return cleaned_thoughts
    
    def log_reasoning_trace(
        self,
        source: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a reasoning trace to the JSONL file
        
        Args:
            source: Source of the reasoning (e.g., 'reasoning_loop', 'explorer', 'architect')
            prompt: Input prompt sent to R1
            response: Response received from R1
            metadata: Additional metadata to log
        """
        try:
            # Extract thought tags
            thoughts = self.extract_thought_tags(response)
            
            # Build log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'source': source,
                'prompt': prompt,
                'response': response,
                'thoughts': thoughts,
                'thought_count': len(thoughts),
                'metadata': metadata or {}
            }
            
            # Check file size and rotate if needed
            self._check_and_rotate()
            
            # Append to JSONL file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.info(
                f"Logged reasoning trace from {source} "
                f"({len(thoughts)} thoughts, {len(response)} chars)"
            )
            
        except Exception as e:
            logger.error(f"Error logging reasoning trace: {str(e)}")
    
    def log_analysis(
        self,
        analysis: Dict[str, Any],
        source: str = "reasoning_loop"
    ):
        """
        Log an analysis result with reasoning traces
        
        Args:
            analysis: Analysis dictionary containing reasoning info
            source: Source of the analysis
        """
        prompt = analysis.get('r1_prompt', '')
        
        # Create simulated response that includes reasoning
        response = f"""
Analysis Result:
- Signal: {analysis.get('signal', 'UNKNOWN')}
- Confidence: {analysis.get('confidence', 0):.2%}
- Regime: {analysis.get('regime', 'UNKNOWN')}

<thought>
Analyzing market conditions in {analysis.get('regime', 'UNKNOWN')} regime.
Current price action suggests {analysis.get('signal', 'HOLD')} with confidence {analysis.get('confidence', 0):.2%}.
Reasoning: {analysis.get('reasoning', 'No reasoning provided')}
</thought>

Final Decision: {analysis.get('signal', 'HOLD')}
"""
        
        metadata = {
            'signal': analysis.get('signal'),
            'confidence': analysis.get('confidence'),
            'regime': analysis.get('regime'),
            'metrics': analysis.get('metrics', {})
        }
        
        self.log_reasoning_trace(source, prompt, response, metadata)
    
    def log_hypothesis(
        self,
        hypothesis: Dict[str, Any],
        source: str = "explorer"
    ):
        """
        Log a hypothesis from the Stochastic Alpha Explorer
        
        Args:
            hypothesis: Hypothesis dictionary
            source: Source (default: explorer)
        """
        prompt = f"Generate novel trading hypothesis for {hypothesis.get('regime', 'UNKNOWN')} regime"
        
        response = f"""
<thought>
Exploring creative trading strategies for {hypothesis.get('regime', 'UNKNOWN')} market conditions.
Analyzing {hypothesis.get('failed_strategies_analyzed', 0)} failed strategies to avoid repeating mistakes.
Considering unconventional approaches and novel signal combinations.
</thought>

Hypothesis: {hypothesis.get('hypothesis', 'No hypothesis')}
Confidence: {hypothesis.get('confidence', 0):.2%}

<thought>
This hypothesis leverages:
- {', '.join(hypothesis.get('suggested_indicators', []))}

Implementation approach:
{chr(10).join('- ' + hint for hint in hypothesis.get('implementation_hints', []))}
</thought>
"""
        
        metadata = {
            'hypothesis': hypothesis.get('hypothesis'),
            'confidence': hypothesis.get('confidence'),
            'regime': hypothesis.get('regime'),
            'temperature': hypothesis.get('temperature')
        }
        
        self.log_reasoning_trace(source, prompt, response, metadata)
    
    def _check_and_rotate(self):
        """Check log file size and rotate if needed"""
        if not self.log_file.exists():
            return
        
        file_size = self.log_file.stat().st_size
        
        if file_size > self.max_size_bytes:
            # Rotate log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_name = f"{self.log_file.stem}_{timestamp}{self.log_file.suffix}"
            rotated_path = self.log_file.parent / rotated_name
            
            self.log_file.rename(rotated_path)
            self.log_file.touch()
            
            logger.info(f"Rotated log file to {rotated_name}")
    
    def read_recent_traces(self, count: int = 10) -> list:
        """
        Read the most recent reasoning traces
        
        Args:
            count: Number of traces to read
            
        Returns:
            List of trace dictionaries
        """
        if not self.log_file.exists():
            return []
        
        try:
            traces = []
            with open(self.log_file, 'r') as f:
                # Read all lines
                lines = f.readlines()
                
                # Get last N lines
                recent_lines = lines[-count:] if len(lines) > count else lines
                
                # Parse JSON
                for line in recent_lines:
                    try:
                        traces.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            return traces
            
        except Exception as e:
            logger.error(f"Error reading traces: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged reasoning traces
        
        Returns:
            Dictionary with statistics
        """
        if not self.log_file.exists():
            return {
                'total_traces': 0,
                'file_size_mb': 0,
                'sources': {}
            }
        
        try:
            total_traces = 0
            sources = {}
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        trace = json.loads(line)
                        total_traces += 1
                        
                        source = trace.get('source', 'unknown')
                        sources[source] = sources.get(source, 0) + 1
                    except json.JSONDecodeError:
                        continue
            
            file_size_mb = self.log_file.stat().st_size / (1024 * 1024)
            
            return {
                'total_traces': total_traces,
                'file_size_mb': round(file_size_mb, 2),
                'sources': sources
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {
                'total_traces': 0,
                'file_size_mb': 0,
                'sources': {},
                'error': str(e)
            }
