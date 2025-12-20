"""
Configuration management for Aether-Evo WEEX Engine
"""
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class WeexConfig(BaseModel):
    """WEEX API configuration"""
    api_key: str = Field(default_factory=lambda: os.getenv("WEEX_API_KEY", ""))
    api_secret: str = Field(default_factory=lambda: os.getenv("WEEX_API_SECRET", ""))
    api_password: str = Field(default_factory=lambda: os.getenv("WEEX_API_PASSWORD", ""))


class DeepSeekConfig(BaseModel):
    """DeepSeek AI configuration"""
    api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    model: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-r1"))


class TradingConfig(BaseModel):
    """Trading parameters configuration"""
    symbol: str = Field(default_factory=lambda: os.getenv("TRADING_SYMBOL", "BTC/USDT"))
    initial_equity: float = Field(default_factory=lambda: float(os.getenv("INITIAL_EQUITY", "1000.0")))
    kill_switch_threshold: float = Field(default_factory=lambda: float(os.getenv("KILL_SWITCH_THRESHOLD", "0.03")))
    stability_lock_hours: int = Field(default_factory=lambda: int(os.getenv("STABILITY_LOCK_HOURS", "12")))
    reasoning_interval_minutes: int = Field(default_factory=lambda: int(os.getenv("REASONING_INTERVAL_MINUTES", "15")))


class AetherConfig(BaseModel):
    """Master configuration for Aether-Evo"""
    weex: WeexConfig = Field(default_factory=WeexConfig)
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
