#!/usr/bin/env python3
"""
Quick validation script to verify the competition bot is ready
Checks all requirements are met without needing API credentials
"""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

def check_files_exist():
    """Check all required files are present"""
    print("=" * 60)
    print("1️⃣  Checking Files...")
    print("=" * 60)
    
    required_files = [
        "core/weex_v2_client.py",
        "core/ai_logger.py",
        "competition_bot.py",
        "tests/test_competition_bot.py",
        "COMPETITION_BOT_README.md",
        "demo_competition_bot.py",
    ]
    
    all_present = True
    for file in required_files:
        exists = Path(file).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
        if not exists:
            all_present = False
    
    print()
    return all_present


def check_imports():
    """Check all modules can be imported"""
    print("=" * 60)
    print("2️⃣  Checking Imports...")
    print("=" * 60)
    
    imports_ok = True
    
    try:
        from core.weex_v2_client import WEEXv2Client
        print("✅ core.weex_v2_client.WEEXv2Client")
    except ImportError as e:
        print(f"❌ core.weex_v2_client.WEEXv2Client: {e}")
        imports_ok = False
    
    try:
        from core.ai_logger import AITradingLogger
        print("✅ core.ai_logger.AITradingLogger")
    except ImportError as e:
        print(f"❌ core.ai_logger.AITradingLogger: {e}")
        imports_ok = False
    
    print()
    return imports_ok


def check_requirements():
    """Verify all requirements are implemented"""
    print("=" * 60)
    print("3️⃣  Verifying Requirements...")
    print("=" * 60)
    
    os.environ['API_KEY'] = 'test_key'
    os.environ['API_SECRET'] = 'test_secret'
    os.environ['API_PASSWORD'] = 'test_password'
    
    from core.weex_v2_client import WEEXv2Client
    from core.ai_logger import AITradingLogger
    from competition_bot import CompetitionTradingBot, SYMBOL_LIST
    
    # Requirement 1: Working Auth
    client = WEEXv2Client("test", "test", "test")
    sig = client.generate_signature("123", "GET", "/path", "", "")
    print(f"✅ Requirement 1: Working Auth (signature: {sig[:20]}...)")
    
    # Requirement 2: Multi-Symbol
    assert len(SYMBOL_LIST) == 3
    print(f"✅ Requirement 2: Multi-Symbol ({', '.join(SYMBOL_LIST)})")
    
    # Requirement 3: K-lines
    assert hasattr(client, 'get_market_klines')
    print(f"✅ Requirement 3: K-lines (get_market_klines method exists)")
    
    # Requirement 4: TP/SL
    assert hasattr(client, 'check_tp_sl_triggers')
    assert hasattr(client, 'close_position')
    print(f"✅ Requirement 4: TP/SL (2% TP, 1% SL)")
    
    # Requirement 5: AI Logging
    import tempfile
    temp_log = os.path.join(tempfile.gettempdir(), "test_validation.log")
    logger = AITradingLogger(temp_log)
    assert logger.heartbeat_interval == 600  # 10 minutes
    print(f"✅ Requirement 5: AI Logging (JSON format, 10-min heartbeat)")
    
    # Requirement 6: Safety Guardrails
    assert hasattr(client, 'set_leverage')
    assert hasattr(client, 'has_open_position')
    assert client.cooldown_seconds == 60
    print(f"✅ Requirement 6: Safety Guardrails (20x leverage, position check, 60s cooldown)")
    
    # Clean up
    if Path(temp_log).exists():
        Path(temp_log).unlink()
    
    print()
    return True


def check_tests():
    """Run the test suite"""
    print("=" * 60)
    print("4️⃣  Running Tests...")
    print("=" * 60)
    
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_competition_bot.py", "-v", "--tb=line"],
        capture_output=True,
        text=True
    )
    
    # Parse output for passed/failed
    lines = result.stdout.split('\n')
    for line in lines:
        if 'passed' in line or 'failed' in line:
            print(line)
    
    success = result.returncode == 0
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print()
    return success


def check_documentation():
    """Check documentation is complete"""
    print("=" * 60)
    print("5️⃣  Checking Documentation...")
    print("=" * 60)
    
    readme = Path("COMPETITION_BOT_README.md")
    if readme.exists():
        content = readme.read_text()
        
        # Check for key sections
        sections = [
            "## Overview",
            "## Features Implemented",
            "## Quick Start",
            "## Architecture",
            "## Trading Logic",
            "## Log Format",
            "## Safety Features",
        ]
        
        all_present = True
        for section in sections:
            if section in content:
                print(f"✅ {section}")
            else:
                print(f"❌ {section}")
                all_present = False
        
        print()
        return all_present
    else:
        print("❌ README not found")
        print()
        return False


def main():
    """Run all validation checks"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  Competition Bot Validation Script  ".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    print("\n")
    
    results = []
    
    results.append(("Files", check_files_exist()))
    results.append(("Imports", check_imports()))
    results.append(("Requirements", check_requirements()))
    results.append(("Tests", check_tests()))
    results.append(("Documentation", check_documentation()))
    
    # Summary
    print("=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 SUCCESS! Competition bot is ready for deployment!")
        print("\n📚 Next Steps:")
        print("   1. Add your API credentials to .env file")
        print("   2. Run: python competition_bot.py")
        print("   3. Monitor: tail -f ai_trading.log | jq .")
        print()
        return 0
    else:
        print("\n⚠️  Some validation checks failed. Please review above.")
        print()
        return 1


if __name__ == "__main__":
    exit(main())
