"""
Aether-Evo: Self-Evolving WEEX Trading Engine
Main orchestrator that coordinates all components
"""
import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

from config import AetherConfig
from discovery_agent import DiscoveryAgent
from reasoning_loop import ReasoningLoop
from architect import Architect
from guardrails import Guardrails
from data.memory import EvolutionMemory
from data.logger import ReasoningLogger
from agents.explorer import StochasticAlphaExplorer
from core.backtester import VectorizedBacktester
import active_logic

# Wild Imagination imports
from agents.narrative import NarrativePulse
from core.adversary import AdversarialAlpha
from core.shadow_engine import ShadowEngine

# Predator Suite imports (Aether-Evo Phase)
from agents.adversary import BehavioralAdversary
from agents.reconciliation_loop import IntelligenceLedger, ReconciliationAuditor
from agents.evolutionary_mutator import EvolutionaryMutator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AetherEvo:
    """
    Aether-Evo: Self-Evolving WEEX Trading Engine
    
    Architecture:
    1. Discovery Agent - Dynamic API mapping
    2. Reasoning Loop - R1 analyzes OHLCV every 15m
    3. Evolution System - Architect rewrites active_logic.py with R1 approval
    4. Guardrails - Safety mechanisms (12h lock, 3% kill-switch, code audit)
    5. Stochastic Alpha Explorer - Generates novel hypotheses every 6h (Phase 3)
    6. Vectorized Backtester - Validates strategies before deployment (Phase 3)
    7. Reasoning Logger - Logs R1 traces for dashboard (Phase 3)
    8. Predator Suite - Behavioral analysis, reconciliation, and evolution (Aether-Evo)
       - BehavioralAdversary - "Dark Mirror" for psychological analysis
       - ReconciliationAuditor - "The Auditor" for prediction validation
       - EvolutionaryMutator - "DNA Patch" for self-improvement
    """
    
    def __init__(self, config: AetherConfig):
        """Initialize Aether-Evo engine"""
        self.config = config
        
        # Initialize components
        logger.info("Initializing Aether-Evo components...")
        
        # Discovery Agent
        self.discovery = DiscoveryAgent(
            api_key=config.weex.api_key,
            api_secret=config.weex.api_secret,
            api_password=config.weex.api_password,
            exchange_id=config.weex.exchange_id
        )
        
        # Guardrails
        self.guardrails = Guardrails(
            initial_equity=config.trading.initial_equity,
            kill_switch_threshold=config.trading.kill_switch_threshold,
            stability_lock_hours=config.trading.stability_lock_hours
        )
        
        # Evolution Memory
        self.evolution_memory = EvolutionMemory()
        
        # Reasoning Loop
        self.reasoning = ReasoningLoop(
            discovery_agent=self.discovery,
            deepseek_config=config.deepseek,
            interval_minutes=config.trading.reasoning_interval_minutes,
            evolution_memory=self.evolution_memory
        )
        
        # Architect
        self.architect = Architect(
            guardrails=self.guardrails,
            logic_file_path="active_logic.py",
            evolution_memory=self.evolution_memory
        )
        
        # Phase 3 Components
        # Reasoning Logger - Telemetry for R1 traces
        self.reasoning_logger = ReasoningLogger()
        
        # Stochastic Alpha Explorer - 6-hour creative hypothesis generation
        self.explorer = StochasticAlphaExplorer(
            deepseek_config=config.deepseek,
            evolution_memory=self.evolution_memory,
            interval_hours=6,
            temperature=1.3
        )
        
        # Vectorized Backtester - Strategy validation
        self.backtester = VectorizedBacktester()
        
        # Phase 5: Wild Imagination modules
        from data.shared_state import get_shared_state
        self.shared_state = get_shared_state()
        
        self.narrative = NarrativePulse(
            whale_threshold_btc=1000.0
        )
        
        self.adversary = AdversarialAlpha(
            flash_crash_pct=-0.20,
            max_drawdown_threshold=0.15
        )
        
        self.shadow_engine = ShadowEngine(
            promotion_threshold_iterations=100,
            sharpe_ratio_threshold=1.2
        )
        
        logger.info("✅ Wild Imagination modules initialized (Adversary, Shadow Engine, Narrative)")
        
        # Predator Suite (Aether-Evo Phase)
        # Initialize the three core agents for behavioral analysis and self-improvement
        self.behavioral_adversary = BehavioralAdversary(
            deepseek_api_key=config.deepseek.api_key,
            model=config.deepseek.model,
            use_shadow_mode=False,  # Will auto-activate on 451 errors
            enable_cot=True
        )
        
        self.intelligence_ledger = IntelligenceLedger(
            db_path="data/intelligence_ledger.db"
        )
        
        self.reconciliation_auditor = ReconciliationAuditor(
            ledger=self.intelligence_ledger,
            price_fetcher=None  # Will be set up with actual price fetcher
        )
        
        self.evolutionary_mutator = EvolutionaryMutator(
            prompts_dir="data/prompts",
            deepseek_api_key=config.deepseek.api_key,
            model=config.deepseek.model,
            evolution_interval_hours=24
        )
        
        logger.info("✅ Predator Suite initialized (Behavioral Adversary, Reconciliation Auditor, Evolutionary Mutator)")
        
        self.running = False
        self.symbol = config.trading.symbol
        
    async def initialize(self):
        """Initialize the system"""
        logger.info("🚀 Aether-Evo initialization started...")
        
        try:
            # Discover exchange capabilities
            logger.info("Discovering WEEX exchange capabilities...")
            capabilities = await self.discovery.discover_capabilities()
            
            logger.info(f"✅ Discovery complete:")
            logger.info(f"   - Available symbols: {len(capabilities['symbols'])}")
            logger.info(f"   - Supported timeframes: {list(capabilities['timeframes'].keys())}")
            
            # Verify trading symbol is available
            if self.symbol not in capabilities['symbols']:
                logger.warning(f"⚠️  Symbol {self.symbol} not found in available symbols")
                logger.info(f"Available symbols: {capabilities['symbols'][:10]}...")
                return False
            
            logger.info(f"✅ Trading symbol {self.symbol} verified")
            
            # Try to fetch initial balance
            try:
                balance = await self.discovery.fetch_balance()
                logger.info(f"✅ Account balance fetched: {balance.get('total', {})}")
            except Exception as e:
                logger.warning(f"⚠️  Could not fetch balance (this is OK for demo): {str(e)}")
            
            logger.info("✅ Aether-Evo initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
    
    async def evolution_check_loop(self):
        """Periodically check if evolution should occur"""
        logger.info("Evolution check loop started...")
        
        while self.running:
            try:
                # Wait for reasoning to produce analysis
                await asyncio.sleep(60)  # Check every minute
                
                # Get latest analysis
                analysis = self.reasoning.get_latest_analysis()
                if not analysis:
                    continue
                
                # Check if evolution is suggested and allowed
                if analysis.get('evolution_suggestion'):
                    logger.info("Evolution suggested by R1, checking guardrails...")
                    
                    # Phase 3: Check if we have a hypothesis from explorer
                    hypothesis = self.explorer.get_latest_hypothesis()
                    if hypothesis:
                        logger.info(f"🔬 Latest Hypothesis: {hypothesis.get('hypothesis')}")
                        # Log hypothesis
                        self.reasoning_logger.log_hypothesis(hypothesis, source="explorer")
                    
                    # Phase 3: Run backtest before evolution
                    logger.info("🔬 Running backtest validation...")
                    can_deploy, reason = self.backtester.validate_for_deployment("active_logic.py")
                    
                    if not can_deploy:
                        logger.warning(f"⚠️ Backtest validation failed: {reason}")
                        logger.info("Evolution blocked due to backtest failure")
                        continue
                    
                    logger.info(f"✅ Backtest validation passed: {reason}")
                    
                    # Attempt evolution
                    evolved = await self.architect.evolve(analysis)
                    
                    if evolved:
                        logger.info("🎉 System evolved! Reloading active_logic module...")
                        # Reload the module to use new logic
                        import importlib
                        importlib.reload(active_logic)
                        logger.info("✅ New logic loaded and active")
                
            except Exception as e:
                logger.error(f"Error in evolution check: {str(e)}")
                await asyncio.sleep(60)
    
    async def trading_loop(self):
        """Main trading execution loop"""
        logger.info("Trading loop started...")
        
        while self.running:
            try:
                # Check kill-switch
                if self.guardrails.is_kill_switch_active():
                    logger.critical("🛑 Kill-switch is active! Trading halted.")
                    await asyncio.sleep(60)
                    continue
                
                # Get latest analysis
                analysis = self.reasoning.get_latest_analysis()
                if not analysis:
                    await asyncio.sleep(30)
                    continue
                
                # Phase 3: Log reasoning trace
                self.reasoning_logger.log_analysis(analysis, source="reasoning_loop")
                
                # Fetch current OHLCV
                ohlcv = await self.discovery.fetch_ohlcv(self.symbol, '15m', 100)
                
                # Calculate indicators using active logic
                indicators = active_logic.calculate_indicators(ohlcv)
                
                # Generate signal using active logic
                signal = active_logic.generate_signal(indicators, analysis)
                
                logger.info(f"📊 Trading Signal: {signal['action']} "
                          f"(Confidence: {signal['confidence']:.2%}) "
                          f"- {signal['reason']}")
                
                # Phase 5: Shadow engine comparison
                if signal['action'] in ['BUY', 'SELL']:
                    current_price = indicators.get('current_price', ohlcv[-1][4] if ohlcv else 50000.0)
                    
                    try:
                        shadow_result = self.shadow_engine.simulate_trade_pair(
                            market_signal=signal['action'].lower(),
                            market_price=current_price
                        )
                        
                        if shadow_result.get('promotion_alert'):
                            logger.warning(
                                f"🚀 PROMOTION ALERT: Shadow strategy outperforming!\n"
                                f"   Shadow Sharpe: {shadow_result['shadow_sharpe']:.2f}\n"
                                f"   Live Sharpe: {shadow_result['live_sharpe']:.2f}"
                            )
                    except Exception as e:
                        logger.error(f"Shadow engine error (non-critical): {e}")
                
                # In production, execute trades here based on signal
                # For now, just log the signal
                
                # Simulate equity update (in production, fetch real balance)
                # For demo, just use a placeholder
                # self.guardrails.update_equity(new_equity)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def status_loop(self):
        """Display system status periodically"""
        logger.info("Status loop started...")
        
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Get guardrails status
                status = self.guardrails.get_status()
                
                logger.info("=" * 60)
                logger.info("📈 AETHER-EVO STATUS")
                logger.info("=" * 60)
                logger.info(f"Kill Switch: {'🛑 ACTIVE' if status['kill_switch_active'] else '✅ Inactive'}")
                logger.info(f"Equity: ${status['current_equity']:.2f} "
                          f"({status['equity_change_pct']:+.2f}%)")
                logger.info(f"Evolution Lock: {'🔒 Locked' if not status['can_evolve'] else '🔓 Unlocked'}")
                
                if status['last_evolution']:
                    logger.info(f"Last Evolution: {status['last_evolution']}")
                    if not status['can_evolve']:
                        logger.info(f"Lock Remaining: {status['stability_lock_remaining']:.1f}h")
                
                # Latest analysis
                analysis = self.reasoning.get_latest_analysis()
                if analysis:
                    logger.info(f"Latest Signal: {analysis['signal']} "
                              f"({analysis['confidence']:.2%})")
                
                # Evolution history
                history = self.architect.get_evolution_history()
                logger.info(f"Total Evolutions: {len(history)}")
                
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"Error in status loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down Aether-Evo...")
        self.running = False
        self.reasoning.stop()
        self.explorer.stop()  # Phase 3: Stop explorer
        logger.info("✅ Shutdown complete")
    
    async def get_current_regime(self):
        """
        Get current market regime for explorer
        Phase 3 helper method
        """
        try:
            analysis = self.reasoning.get_latest_analysis()
            if analysis:
                return analysis.get('regime', 'UNKNOWN')
            return 'UNKNOWN'
        except:
            return 'UNKNOWN'
    
    async def explorer_loop(self):
        """
        Run the Stochastic Alpha Explorer loop
        Phase 3: Generates novel hypotheses every 6 hours
        """
        logger.info("🔍 Starting Stochastic Alpha Explorer loop...")
        
        # Create callback for getting current regime
        async def regime_callback():
            return await self.get_current_regime()
        
        # Run the explorer loop
        await self.explorer.run_loop(regime_callback)
    
    async def narrative_loop(self):
        """Monitor whale activity every 5 minutes"""
        logger.info("🐋 Narrative monitoring started...")
        
        while self.running:
            try:
                # Mock whale inflow (replace with real exchange API data in production)
                # TODO: Integrate with actual whale alert service or exchange API
                mock_inflow_btc = 500.0
                
                result = self.narrative.check_whale_inflow(mock_inflow_btc)
                
                if result.get('is_whale_event'):
                    logger.warning(f"🐋 ALERT: Whale event detected - {result['exchange_inflow_btc']:.2f} BTC")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in narrative loop: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def predator_suite_loop(self):
        """
        Predator Suite Loop - Behavioral Analysis, Reconciliation, and Evolution
        
        This loop orchestrates the three Predator Suite agents:
        1. BehavioralAdversary - Analyzes market psychology every 15 minutes
        2. ReconciliationAuditor - Audits predictions every 1h, 4h, 12h
        3. EvolutionaryMutator - Evolves prompts every 24 hours
        """
        logger.info("🎯 Predator Suite monitoring started...")
        
        # Track last audit times
        last_audit_1h = datetime.now()
        last_audit_4h = datetime.now()
        last_audit_12h = datetime.now()
        last_evolution = datetime.now()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # 1. Run behavioral analysis with latest market data
                try:
                    ohlcv = await self.discovery.fetch_ohlcv(self.symbol, '15m', 100)
                    if ohlcv:
                        current_price = ohlcv[-1][4]
                        
                        # Calculate some basic indicators for analysis
                        closes = [candle[4] for candle in ohlcv[-20:]]
                        rsi = self._calculate_simple_rsi(closes)
                        price_change = ((closes[-1] - closes[0]) / closes[0]) * 100
                        
                        market_data = {
                            'price': current_price,
                            'rsi': rsi,
                            'price_change_pct': price_change,
                            'volume': ohlcv[-1][5] if len(ohlcv[-1]) > 5 else 0,
                            'recent_lows': [min([c[3] for c in ohlcv[-i-5:-i]]) for i in range(0, 15, 5)]
                        }
                        
                        # Get sentiment from narrative pulse
                        sentiment = "Neutral"
                        try:
                            narrative_state = self.narrative.get_current_narrative()
                            if narrative_state:
                                sentiment = narrative_state.get('sentiment', 'Neutral')
                        except:
                            pass
                        
                        # Run behavioral analysis
                        analysis = self.behavioral_adversary.analyze_psychology(
                            market_data,
                            sentiment=sentiment,
                            narrative=None
                        )
                        
                        # Record prediction in ledger
                        if analysis.get('detected_archetype') != 'NEUTRAL':
                            self.intelligence_ledger.record_prediction(
                                predicted_bias=analysis['predicted_bias'],
                                predicted_outcome=analysis['predicted_outcome'],
                                confidence=analysis['confidence'],
                                market_regime=analysis['market_regime'],
                                archetype=analysis['detected_archetype'],
                                signal=analysis['signal'],
                                price_at_prediction=current_price
                            )
                            
                            logger.info(f"🎯 Behavioral Analysis: {analysis['detected_archetype']} "
                                      f"-> {analysis['predicted_outcome']} (Confidence: {analysis['confidence']:.2f})")
                
                except Exception as e:
                    logger.error(f"Error in behavioral analysis: {e}")
                
                # 2. Run reconciliation audits at appropriate intervals
                try:
                    # Get current price for audits
                    ohlcv = await self.discovery.fetch_ohlcv(self.symbol, '1m', 1)
                    current_price = ohlcv[-1][4] if ohlcv else None
                    
                    if current_price:
                        # 1-hour audit
                        if (current_time - last_audit_1h).total_seconds() >= 3600:
                            logger.info("🔍 Running 1-hour reconciliation audit...")
                            self.reconciliation_auditor._audit_timeframe("1h", 1, current_price)
                            last_audit_1h = current_time
                        
                        # 4-hour audit
                        if (current_time - last_audit_4h).total_seconds() >= 14400:
                            logger.info("🔍 Running 4-hour reconciliation audit...")
                            self.reconciliation_auditor._audit_timeframe("4h", 4, current_price)
                            last_audit_4h = current_time
                        
                        # 12-hour audit
                        if (current_time - last_audit_12h).total_seconds() >= 43200:
                            logger.info("🔍 Running 12-hour reconciliation audit...")
                            self.reconciliation_auditor._audit_timeframe("12h", 12, current_price)
                            last_audit_12h = current_time
                            
                            # Display audit statistics
                            stats = self.intelligence_ledger.get_statistics()
                            logger.info(f"📊 Prediction Stats: Total={stats['total_predictions']}, "
                                      f"Avg Score 1h={stats['avg_score_1h']:.2f}")
                
                except Exception as e:
                    logger.error(f"Error in reconciliation audit: {e}")
                
                # 3. Run evolutionary mutation every 24 hours
                try:
                    if (current_time - last_evolution).total_seconds() >= 86400:
                        logger.info("🧬 Running evolutionary mutation cycle...")
                        
                        # Get failed predictions
                        failed_predictions = self.reconciliation_auditor.get_failed_predictions_for_learning(top_n=5)
                        
                        if failed_predictions:
                            logger.info(f"Found {len(failed_predictions)} failed predictions for learning")
                            
                            # Evolve the prompt
                            new_prompt = self.evolutionary_mutator.evolve_prompt(
                                failed_predictions,
                                force=True
                            )
                            
                            if new_prompt:
                                logger.info(f"✅ Prompt evolved to v{self.evolutionary_mutator.current_version}")
                            else:
                                logger.info("ℹ️  No prompt evolution this cycle")
                        else:
                            logger.info("ℹ️  No failed predictions to learn from")
                        
                        last_evolution = current_time
                
                except Exception as e:
                    logger.error(f"Error in evolutionary mutation: {e}")
                
                # Wait 15 minutes before next cycle (aligned with reasoning interval)
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Error in predator suite loop: {e}")
                await asyncio.sleep(60)
    
    def _calculate_simple_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate simple RSI for behavioral analysis"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def run(self):
        """Run the Aether-Evo engine"""
        logger.info("=" * 60)
        logger.info("🌟 AETHER-EVO: SELF-EVOLVING WEEX ENGINE 🌟")
        logger.info("Predator Suite: Behavioral Analysis & Self-Evolution")
        logger.info("=" * 60)
        
        # Initialize
        initialized = await self.initialize()
        if not initialized:
            logger.error("Initialization failed. Exiting.")
            return
        
        self.running = True
        
        try:
            # Start all loops concurrently (including Predator Suite)
            await asyncio.gather(
                self.reasoning.run_loop(self.symbol),
                self.evolution_check_loop(),
                self.trading_loop(),
                self.status_loop(),
                self.explorer_loop(),  # Phase 3: Explorer agent
                self.narrative_loop(),  # Phase 5: Narrative monitoring
                self.predator_suite_loop(),  # Predator Suite: Behavioral analysis & evolution
            )
        except KeyboardInterrupt:
            logger.info("\n👋 Shutdown requested by user...")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    try:
        # Load configuration
        config = AetherConfig()
        
        # Validate configuration
        if not config.weex.api_key or config.weex.api_key == "your_api_key_here":
            logger.warning("⚠️  WEEX API credentials not configured!")
            logger.info("Please set credentials in .env file (see .env.example)")
            logger.info("Running in demo mode with limited functionality...")
        
        # Create and run Aether-Evo
        aether = AetherEvo(config)
        await aether.run()
        
    except Exception as e:
        logger.error(f"Failed to start Aether-Evo: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
