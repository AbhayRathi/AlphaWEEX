#!/usr/bin/env python3
"""
Final Integrity Check Script for AlphaWEEX

This script verifies:
1. All core modules can be imported successfully
2. SharedState singleton is accessible
3. All tests pass (exit code 0)
"""
import sys
import os
import subprocess
import logging

# Add parent directory to path so imports work
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_module_imports():
    """Import all core modules and verify they load correctly"""
    logger.info("=" * 60)
    logger.info("STEP 1: Checking Core Module Imports")
    logger.info("=" * 60)
    
    modules = [
        # Core modules
        ('discovery_agent', 'DiscoveryAgent'),
        ('reasoning_loop', 'ReasoningLoop'),
        ('architect', 'Architect'),
        ('guardrails', 'Guardrails'),
        ('active_logic', None),
        
        # Data modules
        ('data.shared_state', 'get_shared_state'),
        ('data.shared_state', 'SharedState'),
        ('data.shared_state', 'RiskLevel'),
        ('data.memory', 'EvolutionMemory'),
        ('data.logger', 'ReasoningLogger'),
        ('data.regime', 'get_regime_metrics'),
        
        # Core components
        ('core.backtester', 'VectorizedBacktester'),
        ('core.oracle', 'TradFiOracle'),
        ('core.weex_client', 'WEEXClient'),
        ('core.adversary', 'AdversarialAlpha'),
        ('core.shadow_engine', 'ShadowEngine'),
        
        # Agents
        ('agents.narrative', 'NarrativePulse'),
        ('agents.explorer', 'StochasticAlphaExplorer'),
        ('agents.perception', 'SentimentAgent'),
        
        # Config
        ('config', 'AetherConfig'),
    ]
    
    failed_imports = []
    
    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
            logger.info(f"✅ {module_path}.{class_name if class_name else ''}")
        except Exception as e:
            logger.error(f"❌ {module_path}.{class_name if class_name else ''}: {str(e)}")
            failed_imports.append((module_path, class_name, str(e)))
    
    if failed_imports:
        logger.error(f"\n❌ {len(failed_imports)} module(s) failed to import")
        return False
    
    logger.info(f"\n✅ All {len(modules)} core modules imported successfully")
    return True


def check_shared_state_singleton():
    """Verify SharedState singleton is accessible and functional"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Verifying SharedState Singleton")
    logger.info("=" * 60)
    
    try:
        from data.shared_state import get_shared_state, RiskLevel
        
        # Get singleton instance
        state1 = get_shared_state()
        logger.info("✅ SharedState singleton instance created")
        
        # Verify it's a singleton (same instance)
        state2 = get_shared_state()
        if state1 is not state2:
            logger.error("❌ SharedState is not a singleton (different instances)")
            return False
        logger.info("✅ SharedState singleton pattern verified")
        
        # Test risk level operations
        state1.set_global_risk_level(RiskLevel.HIGH)
        risk = state1.get_global_risk_level()
        if risk != RiskLevel.HIGH:
            logger.error(f"❌ Risk level mismatch: expected HIGH, got {risk}")
            return False
        logger.info("✅ Risk level management working")
        
        # Test sentiment multiplier
        state1.set_sentiment_multiplier(0.8)
        sentiment = state1.get_sentiment_multiplier()
        if sentiment != 0.8:
            logger.error(f"❌ Sentiment multiplier mismatch: expected 0.8, got {sentiment}")
            return False
        logger.info("✅ Sentiment multiplier working")
        
        # Test whale dump risk
        state1.set_whale_dump_risk(True)
        whale_risk = state1.get_whale_dump_risk()
        if not whale_risk:
            logger.error("❌ Whale dump risk flag not set correctly")
            return False
        logger.info("✅ Whale dump risk flag working")
        
        # Test complete state snapshot
        snapshot = state1.get_all_state()
        if not isinstance(snapshot, dict):
            logger.error("❌ State snapshot is not a dictionary")
            return False
        logger.info("✅ State snapshot generation working")
        
        logger.info("\n✅ SharedState singleton fully functional")
        return True
        
    except Exception as e:
        logger.error(f"❌ SharedState verification failed: {str(e)}")
        return False


def run_tests():
    """Run all tests and verify exit code is 0"""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Running Test Suite (make test)")
    logger.info("=" * 60)
    
    try:
        # Run make test
        result = subprocess.run(
            ['make', 'test'],
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes timeout
        )
        
        if result.returncode == 0:
            logger.info("\n✅ All tests passed (exit code 0)")
            
            # Extract test summary from output
            for line in result.stdout.split('\n'):
                if 'passed' in line.lower():
                    logger.info(f"   {line.strip()}")
            
            return True
        else:
            logger.error(f"\n❌ Tests failed with exit code {result.returncode}")
            logger.error("STDERR:")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Tests timed out after 3 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to run tests: {str(e)}")
        return False


def main():
    """Run all integrity checks"""
    logger.info("\n" + "=" * 60)
    logger.info("AlphaWEEX Final Integrity Check")
    logger.info("=" * 60)
    
    results = []
    
    # Step 1: Module imports
    results.append(("Module Imports", check_module_imports()))
    
    # Step 2: SharedState singleton
    results.append(("SharedState Singleton", check_shared_state_singleton()))
    
    # Step 3: Test suite
    results.append(("Test Suite", run_tests()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INTEGRITY CHECK SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("\n🎉 ALL INTEGRITY CHECKS PASSED 🎉")
        logger.info("AlphaWEEX is ready for competition!\n")
        return 0
    else:
        logger.error("\n⚠️  INTEGRITY CHECK FAILED ⚠️")
        logger.error("Please fix the issues above before deployment\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
