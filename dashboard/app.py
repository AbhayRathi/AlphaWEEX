"""
Reasoning Dashboard for AlphaWEEX Phase 3
Streamlit-based visualization of the system's "Brain"
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.logger import ReasoningLogger
from data.memory import EvolutionMemory


def load_reasoning_logs(log_file: str = "../data/reasoning_logs.jsonl") -> List[Dict]:
    """Load reasoning logs from JSONL file"""
    logger = ReasoningLogger(log_file)
    return logger.read_recent_traces(count=100)


def load_evolution_history(history_file: str = "../data/evolution_history.json") -> Dict:
    """Load evolution history"""
    memory = EvolutionMemory(history_file)
    return memory.data


def parse_thought_tags(response: str) -> List[str]:
    """Extract thought tags from response"""
    import re
    pattern = r'<thought>(.*?)</thought>'
    thoughts = re.findall(pattern, response, re.DOTALL)
    return [thought.strip() for thought in thoughts]


def render_thinking_log():
    """Render the Thinking Log section"""
    st.header("🧠 The Thinking Log")
    st.markdown("*Real-time reasoning traces from DeepSeek-R1*")
    
    try:
        # Load recent traces
        traces = load_reasoning_logs()
        
        if not traces:
            st.info("No reasoning traces available yet. The system will start logging once it begins operating.")
            return
        
        # Get latest trace
        latest_trace = traces[-1] if traces else None
        
        if latest_trace:
            st.subheader("Latest Decision")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Source", latest_trace.get('source', 'Unknown'))
            with col2:
                st.metric("Timestamp", 
                         datetime.fromisoformat(latest_trace['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
            with col3:
                st.metric("Thoughts", latest_trace.get('thought_count', 0))
            
            # Display thoughts
            st.markdown("#### Reasoning Process")
            thoughts = latest_trace.get('thoughts', [])
            
            if thoughts:
                for i, thought in enumerate(thoughts, 1):
                    with st.expander(f"Thought {i}"):
                        st.markdown(thought)
            else:
                st.info("No thought tags found in this trace")
            
            # Display metadata
            if latest_trace.get('metadata'):
                st.markdown("#### Decision Metadata")
                metadata = latest_trace['metadata']
                
                # Format metadata nicely
                for key, value in metadata.items():
                    if key == 'metrics' and isinstance(value, dict):
                        st.json(value)
                    elif isinstance(value, float):
                        st.text(f"{key}: {value:.4f}")
                    else:
                        st.text(f"{key}: {value}")
        
        # Show trace history
        st.markdown("---")
        st.subheader("Recent Reasoning Traces")
        
        # Convert to DataFrame for display
        trace_df = pd.DataFrame([
            {
                'Timestamp': datetime.fromisoformat(t['timestamp']).strftime("%Y-%m-%d %H:%M"),
                'Source': t.get('source', 'Unknown'),
                'Thoughts': t.get('thought_count', 0),
                'Signal': t.get('metadata', {}).get('signal', 'N/A'),
                'Confidence': f"{t.get('metadata', {}).get('confidence', 0):.1%}" if t.get('metadata', {}).get('confidence') else 'N/A'
            }
            for t in traces[-10:]
        ])
        
        st.dataframe(trace_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading reasoning logs: {str(e)}")


def render_strategy_lineage():
    """Render the Strategy Lineage section"""
    st.header("🧬 Strategy Lineage")
    st.markdown("*Visual history of strategy evolution*")
    
    try:
        # Load evolution history
        history = load_evolution_history()
        evolutions = history.get('evolutions', [])
        
        if not evolutions:
            st.info("No evolutions recorded yet. The system will evolve as it learns.")
            
            # Show sample lineage
            st.markdown("#### Sample Evolution Path")
            sample_lineage = """
            ```
            Version 1.0 (Initial)
                ↓
            Version 1.1 (Added RSI indicator)
                ↓
            Version 1.2 (Regime-aware logic)
                ↓
            Version 2.0 (Current)
            ```
            """
            st.markdown(sample_lineage)
            return
        
        # Display evolution timeline
        st.subheader("Evolution Timeline")
        
        # Create timeline visualization
        timeline_data = []
        for i, evo in enumerate(evolutions):
            timestamp = datetime.fromisoformat(evo['timestamp'])
            timeline_data.append({
                'Version': f"v{i+1}",
                'Timestamp': timestamp,
                'Reason': evo.get('reason', 'Unknown'),
                'PnL': evo.get('final_pnl', evo.get('current_pnl', 'Pending'))
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        # Plot timeline
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timeline_df['Timestamp'],
            y=timeline_df.index,
            mode='markers+lines+text',
            marker=dict(size=15, color='lightblue'),
            text=timeline_df['Version'],
            textposition='top center',
            name='Evolutions'
        ))
        
        fig.update_layout(
            title="Strategy Evolution Timeline",
            xaxis_title="Date",
            yaxis_title="Version",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display evolution details
        st.subheader("Evolution Details")
        
        for i, evo in enumerate(evolutions):
            with st.expander(f"Version {i+1} - {evo.get('reason', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Timestamp:**")
                    st.text(datetime.fromisoformat(evo['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
                    
                    st.markdown("**Reason:**")
                    st.text(evo.get('reason', 'Unknown'))
                    
                    st.markdown("**Initial Equity:**")
                    st.text(f"${evo.get('initial_equity', 0):.2f}")
                
                with col2:
                    st.markdown("**Suggestion:**")
                    st.text(evo.get('suggestion', 'None'))
                    
                    pnl = evo.get('final_pnl', evo.get('current_pnl', 'Pending'))
                    st.markdown("**Performance (PnL):**")
                    if isinstance(pnl, (int, float)):
                        st.text(f"${pnl:.2f}")
                    else:
                        st.text(pnl)
                    
                    status = "✅ Evaluated" if evo.get('evaluated') else "⏳ Pending"
                    st.markdown("**Status:**")
                    st.text(status)
        
        # Show blacklisted parameters
        blacklisted = history.get('blacklisted_parameters', [])
        if blacklisted:
            st.markdown("---")
            st.subheader("⚠️ Blacklisted Parameters")
            st.markdown(f"*{len(blacklisted)} parameter set(s) have failed and are blacklisted*")
            
            for i, bl in enumerate(blacklisted[-5:]):  # Show last 5
                with st.expander(f"Blacklist {i+1} - {bl.get('reason', 'Unknown')}"):
                    st.json(bl.get('parameters', {}))
        
    except Exception as e:
        st.error(f"Error loading evolution history: {str(e)}")


def render_live_metrics():
    """Render the Live Metrics section"""
    st.header("📊 Live Metrics")
    st.markdown("*Real-time system performance*")
    
    try:
        # Load evolution history for PnL
        history = load_evolution_history()
        evolutions = history.get('evolutions', [])
        
        # Calculate metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_evolutions = len(evolutions)
            st.metric("Total Evolutions", total_evolutions)
        
        with col2:
            blacklisted = len(history.get('blacklisted_parameters', []))
            st.metric("Blacklisted", blacklisted)
        
        with col3:
            success_rate = 0.0
            if evolutions:
                evaluated = [e for e in evolutions if e.get('evaluated')]
                if evaluated:
                    success_rate = ((len(evaluated) - blacklisted) / len(evaluated)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            # Kill-switch status (simulated)
            kill_switch_active = False
            st.metric("Kill-Switch", "🟢 Inactive" if not kill_switch_active else "🔴 ACTIVE")
        
        # PnL Chart
        st.subheader("PnL vs Kill-Switch Threshold")
        
        # Generate sample PnL data
        if evolutions:
            pnl_data = []
            for i, evo in enumerate(evolutions):
                pnl = evo.get('final_pnl', evo.get('current_pnl', 0))
                if isinstance(pnl, (int, float)):
                    pnl_data.append({
                        'Version': f"v{i+1}",
                        'PnL': pnl,
                        'Timestamp': datetime.fromisoformat(evo['timestamp'])
                    })
            
            if pnl_data:
                pnl_df = pd.DataFrame(pnl_data)
                
                fig = go.Figure()
                
                # PnL line
                fig.add_trace(go.Scatter(
                    x=pnl_df['Timestamp'],
                    y=pnl_df['PnL'],
                    mode='lines+markers',
                    name='PnL',
                    line=dict(color='green')
                ))
                
                # 3% kill-switch threshold line (assuming initial equity of 1000)
                threshold = -30  # 3% of 1000
                fig.add_hline(
                    y=threshold,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Kill-Switch Threshold (-3%)"
                )
                
                fig.update_layout(
                    title="PnL Over Time",
                    xaxis_title="Date",
                    yaxis_title="PnL ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No PnL data available yet")
        
        # Current system status
        st.markdown("---")
        st.subheader("System Status")
        
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.markdown("**Reasoning Loop:**")
            st.text("🟢 Running")
            
            st.markdown("**Evolution Lock:**")
            if evolutions:
                last_evo = evolutions[-1]
                last_time = datetime.fromisoformat(last_evo['timestamp'])
                hours_since = (datetime.now() - last_time).total_seconds() / 3600
                if hours_since < 12:
                    st.text(f"🔒 Locked ({12 - hours_since:.1f}h remaining)")
                else:
                    st.text("🔓 Unlocked")
            else:
                st.text("🔓 Unlocked (No evolutions yet)")
        
        with status_col2:
            st.markdown("**Explorer Agent:**")
            st.text("🟢 Running (6h cycle)")
            
            st.markdown("**Backtester:**")
            st.text("✅ Ready")
        
    except Exception as e:
        st.error(f"Error loading metrics: {str(e)}")


def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="AlphaWEEX Dashboard",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 AlphaWEEX Reasoning Dashboard")
    st.markdown("*Phase 3: The Alpha Factory & Reasoning Visualizer*")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Thinking Log", "Strategy Lineage", "Live Metrics"]
    )
    
    if page == "Overview":
        st.markdown("## System Overview")
        st.markdown("""
        Welcome to the AlphaWEEX Reasoning Dashboard! This dashboard visualizes the 
        "brain" of the autonomous trading system.
        
        ### Features
        - **Thinking Log**: View real-time reasoning traces from DeepSeek-R1
        - **Strategy Lineage**: Visualize how strategies evolved over time
        - **Live Metrics**: Monitor system performance and safety thresholds
        
        ### Quick Stats
        """)
        
        # Display all metrics in overview
        col1, col2, col3 = st.columns(3)
        
        try:
            history = load_evolution_history()
            traces = load_reasoning_logs()
            
            with col1:
                st.metric("Total Evolutions", len(history.get('evolutions', [])))
            with col2:
                st.metric("Reasoning Traces", len(traces))
            with col3:
                blacklisted = len(history.get('blacklisted_parameters', []))
                st.metric("Blacklisted Params", blacklisted)
        except:
            st.info("Loading system data...")
        
        st.markdown("---")
        st.markdown("Use the navigation sidebar to explore different sections of the dashboard.")
    
    elif page == "Thinking Log":
        render_thinking_log()
    
    elif page == "Strategy Lineage":
        render_strategy_lineage()
    
    elif page == "Live Metrics":
        render_live_metrics()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**AlphaWEEX Phase 3**")
    st.sidebar.markdown("Built with Streamlit")


if __name__ == "__main__":
    main()
