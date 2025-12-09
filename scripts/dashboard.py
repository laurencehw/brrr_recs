"""
South African Economic Reform Dashboard

Interactive Streamlit dashboard for exploring BRRR recommendations
correlated with economic indicators and load-shedding data.

Run with: streamlit run scripts/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

# Page config
st.set_page_config(
    page_title="SA Economic Reform Dashboard",
    page_icon="🇿🇦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"
DATA_DIR = BASE_DIR / "data" / "economic_context"


@st.cache_data
def load_recommendations():
    """Load BRRR recommendations"""
    json_path = ANALYSIS_DIR / "recommendations.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    return pd.DataFrame()


@st.cache_data
def load_economic_context():
    """Load economic context with load-shedding"""
    path = ANALYSIS_DIR / "economic_context_with_loadshedding.csv"
    if path.exists():
        return pd.read_csv(path)
    # Fallback to basic economic context
    path = ANALYSIS_DIR / "economic_context_annual.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def load_loadshedding_data():
    """Load detailed load-shedding data"""
    json_path = ANALYSIS_DIR / "loadshedding_detailed.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@st.cache_data
def load_prioritization_summary():
    """Load prioritization summary"""
    path = ANALYSIS_DIR / "prioritization_summary.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def create_economic_timeline(econ_df):
    """Create economic indicators timeline chart"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            'Unemployment Rate (%)',
            'Electricity Availability (GWh)',
            'Load-Shedding Severity'
        )
    )
    
    # Unemployment
    if 'unemployment_rate' in econ_df.columns:
        fig.add_trace(
            go.Scatter(
                x=econ_df['year'],
                y=econ_df['unemployment_rate'],
                mode='lines+markers',
                name='Unemployment %',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
    
    # Electricity
    if 'electricity_gwh' in econ_df.columns:
        fig.add_trace(
            go.Scatter(
                x=econ_df['year'],
                y=econ_df['electricity_gwh'],
                mode='lines+markers',
                name='Electricity GWh',
                line=dict(color='#f39c12', width=3),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
    
    # Load-shedding days
    if 'days_with_loadshedding' in econ_df.columns:
        colors = ['#27ae60' if d < 50 else '#f39c12' if d < 150 else '#e74c3c' 
                  for d in econ_df['days_with_loadshedding'].fillna(0)]
        fig.add_trace(
            go.Bar(
                x=econ_df['year'],
                y=econ_df['days_with_loadshedding'],
                name='Load-shedding Days',
                marker_color=colors
            ),
            row=3, col=1
        )
    
    fig.update_layout(
        height=700,
        showlegend=False,
        title_text="South African Economic Context (2015-2025)"
    )
    
    return fig


def create_loadshedding_chart(ls_data):
    """Create load-shedding visualization"""
    if not ls_data or 'annual_data' not in ls_data:
        return None
    
    years = []
    days = []
    stages = []
    costs = []
    severities = []
    
    for year, data in ls_data['annual_data'].items():
        years.append(int(year))
        days.append(data['days_with_loadshedding'])
        stages.append(data['max_stage'])
        costs.append(data['total_hours_estimated'] * 200 / 1000)  # R billion
        severities.append(data['severity'])
    
    df = pd.DataFrame({
        'year': years,
        'days': days,
        'max_stage': stages,
        'cost_rbillion': costs,
        'severity': severities
    }).sort_values('year')
    
    # Create combined chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Days of Load-Shedding', 'Estimated Economic Cost (R Billion)')
    )
    
    # Color by severity
    color_map = {'low': '#27ae60', 'moderate': '#f39c12', 'severe': '#e67e22', 'critical': '#e74c3c'}
    colors = [color_map.get(s, '#95a5a6') for s in df['severity']]
    
    fig.add_trace(
        go.Bar(x=df['year'], y=df['days'], marker_color=colors, name='Days'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=df['year'], y=df['cost_rbillion'], marker_color=colors, name='Cost'),
        row=2, col=1
    )
    
    fig.update_layout(height=500, showlegend=False, title_text="Load-Shedding Impact")
    
    return fig


def create_recommendations_by_sector(recs_df):
    """Create recommendations by sector chart"""
    if recs_df.empty or 'sector' not in recs_df.columns:
        return None
    
    sector_counts = recs_df['sector'].value_counts().reset_index()
    sector_counts.columns = ['sector', 'count']
    
    fig = px.pie(
        sector_counts,
        values='count',
        names='sector',
        title='BRRR Recommendations by Sector',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig


def create_recommendations_timeline(recs_df):
    """Create recommendations over time"""
    if recs_df.empty or 'year' not in recs_df.columns:
        return None
    
    yearly = recs_df.groupby('year').size().reset_index(name='count')
    
    fig = px.bar(
        yearly,
        x='year',
        y='count',
        title='BRRR Recommendations by Year',
        color='count',
        color_continuous_scale='Blues'
    )
    
    return fig


def create_correlation_chart(econ_df, recs_df):
    """Create correlation between load-shedding and energy recommendations"""
    if econ_df.empty or recs_df.empty:
        return None
    
    # Count energy recommendations by year
    if 'sector' in recs_df.columns and 'year' in recs_df.columns:
        energy_recs = recs_df[recs_df['sector'].str.lower().str.contains('energy', na=False)]
        yearly_energy = energy_recs.groupby('year').size().reset_index(name='energy_recs')
        
        # Merge with economic data
        if 'days_with_loadshedding' in econ_df.columns:
            merged = econ_df.merge(yearly_energy, on='year', how='left')
            merged['energy_recs'] = merged['energy_recs'].fillna(0)
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=merged['year'],
                    y=merged['days_with_loadshedding'],
                    name='Load-shedding Days',
                    marker_color='#e74c3c',
                    opacity=0.7
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(
                    x=merged['year'],
                    y=merged['energy_recs'],
                    name='Energy Recommendations',
                    mode='lines+markers',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=10)
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title='Load-Shedding vs Energy Sector Recommendations',
                height=400
            )
            fig.update_yaxes(title_text="Load-shedding Days", secondary_y=False)
            fig.update_yaxes(title_text="Energy Recommendations", secondary_y=True)
            
            return fig
    
    return None


# Main app
def main():
    # Header
    st.title("🇿🇦 South African Economic Reform Dashboard")
    st.markdown("""
    Analysis of **10 years of Parliamentary Budget Review and Recommendation Reports (BRRR)**
    correlated with economic indicators and load-shedding data.
    """)
    
    # Load data
    recs_df = load_recommendations()
    econ_df = load_economic_context()
    ls_data = load_loadshedding_data()
    priority_data = load_prioritization_summary()
    
    # Sidebar
    st.sidebar.header("📊 Dashboard Controls")
    
    view = st.sidebar.radio(
        "Select View",
        ["Overview", "Economic Context", "Load-Shedding Crisis", "Recommendations", "Correlations"]
    )
    
    # Key metrics at top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_recs = len(recs_df) if not recs_df.empty else 5256
        st.metric("Total Recommendations", f"{total_recs:,}")
    
    with col2:
        if ls_data and 'summary' in ls_data:
            total_days = ls_data['summary']['total_days_loadshedding']
        else:
            total_days = 944
        st.metric("Days of Load-Shedding", f"{total_days:,}")
    
    with col3:
        if not econ_df.empty and 'unemployment_rate' in econ_df.columns:
            latest_unemp = econ_df['unemployment_rate'].iloc[-2]  # 2024
            st.metric("Unemployment Rate (2024)", f"{latest_unemp:.1f}%")
        else:
            st.metric("Unemployment Rate (2024)", "32.6%")
    
    with col4:
        if ls_data and 'summary' in ls_data:
            cost = ls_data['summary']['total_estimated_cost_rbillion']
        else:
            cost = 2120
        st.metric("Est. Load-Shedding Cost", f"R{cost:,.0f}bn")
    
    st.divider()
    
    # Main content based on view
    if view == "Overview":
        st.header("📈 Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not econ_df.empty:
                fig = create_economic_timeline(econ_df)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Key Findings")
            st.markdown("""
            ### 📊 BRRR Analysis (2015-2025)
            - **5,256** total recommendations analyzed
            - **441** Quick Wins identified
            - **2,060** High Priority recommendations
            - **6** Priority sectors covered
            
            ### ⚡ Energy Crisis Impact
            - Load-shedding peaked in **2022-2023**
            - First Stage 6 in December **2019**
            - Stability returned March **2024**
            
            ### 💼 Economic Context
            - Unemployment rose from 25% to 34%
            - Electricity availability declined 11%
            - COVID-19 caused GDP contraction in 2020
            """)
    
    elif view == "Economic Context":
        st.header("📊 Economic Context (2015-2025)")
        
        if not econ_df.empty:
            fig = create_economic_timeline(econ_df)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Data Table")
            display_cols = ['year', 'unemployment_rate', 'electricity_gwh', 
                          'gdp_growth_pct', 'days_with_loadshedding', 'max_stage']
            available_cols = [c for c in display_cols if c in econ_df.columns]
            st.dataframe(econ_df[available_cols], use_container_width=True)
        else:
            st.warning("Economic context data not available. Run add_economic_context.py first.")
    
    elif view == "Load-Shedding Crisis":
        st.header("⚡ Load-Shedding Crisis Analysis")
        
        if ls_data:
            fig = create_loadshedding_chart(ls_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Key events timeline
            st.subheader("📅 Key Events Timeline")
            
            for year in sorted(ls_data.get('annual_data', {}).keys(), key=int):
                data = ls_data['annual_data'][year]
                severity = data['severity']
                emoji = {'low': '🟢', 'moderate': '🟡', 'severe': '🟠', 'critical': '🔴'}.get(severity, '⚪')
                
                with st.expander(f"{emoji} **{year}** - {data['period']} ({data['days_with_loadshedding']} days)"):
                    st.markdown(f"**Max Stage:** {data['max_stage']}")
                    st.markdown(f"**Estimated Hours:** {data['total_hours_estimated']:,}")
                    st.markdown("**Key Events:**")
                    for event in data['key_events']:
                        st.markdown(f"- {event}")
            
            # Stage definitions
            st.subheader("📖 Load-Shedding Stages Explained")
            if 'stage_definitions' in ls_data:
                stages_df = pd.DataFrame([
                    {
                        'Stage': f"Stage {i}",
                        'MW Removed': f"{ls_data['stage_definitions'][f'stage_{i}']['mw_removed']:,}",
                        'Users Affected': f"{ls_data['stage_definitions'][f'stage_{i}']['percent_affected']}%",
                        'Hours per 4 Days': ls_data['stage_definitions'][f'stage_{i}']['hours_per_4_days']
                    }
                    for i in range(1, 9)
                ])
                st.table(stages_df)
        else:
            st.warning("Load-shedding data not available. Run add_loadshedding_data.py first.")
    
    elif view == "Recommendations":
        st.header("📋 BRRR Recommendations Analysis")
        
        if not recs_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = create_recommendations_by_sector(recs_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = create_recommendations_timeline(recs_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Filter recommendations
            st.subheader("🔍 Explore Recommendations")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'sector' in recs_df.columns:
                    sectors = ['All'] + sorted(recs_df['sector'].dropna().unique().tolist())
                    selected_sector = st.selectbox("Sector", sectors)
            with col2:
                if 'year' in recs_df.columns:
                    years = ['All'] + sorted(recs_df['year'].dropna().unique().tolist())
                    selected_year = st.selectbox("Year", years)
            with col3:
                search = st.text_input("Search keywords")
            
            # Filter
            filtered = recs_df.copy()
            if selected_sector != 'All' and 'sector' in filtered.columns:
                filtered = filtered[filtered['sector'] == selected_sector]
            if selected_year != 'All' and 'year' in filtered.columns:
                filtered = filtered[filtered['year'] == selected_year]
            if search and 'recommendation' in filtered.columns:
                filtered = filtered[filtered['recommendation'].str.contains(search, case=False, na=False)]
            
            st.markdown(f"**Showing {len(filtered):,} recommendations**")
            
            if 'recommendation' in filtered.columns:
                display_cols = ['year', 'sector', 'recommendation']
                available = [c for c in display_cols if c in filtered.columns]
                st.dataframe(filtered[available].head(100), use_container_width=True)
        else:
            st.info("Recommendations data not loaded. The recommendations.json file may be excluded from git.")
            
            # Show summary stats instead
            st.subheader("📊 Summary Statistics")
            st.markdown("""
            Based on analysis of 50 BRRR reports (2015-2025):
            
            | Sector | Reports | Recommendations |
            |--------|---------|-----------------|
            | Energy | 6 | ~850 |
            | Labour | 6 | ~720 |
            | Finance | 18 | ~1,400 |
            | Science & Tech | 5 | ~480 |
            | Infrastructure | 8 | ~890 |
            | Trade | 7 | ~916 |
            | **Total** | **50** | **~5,256** |
            """)
    
    elif view == "Correlations":
        st.header("🔗 Correlations Analysis")
        
        if not econ_df.empty and not recs_df.empty:
            fig = create_correlation_chart(econ_df, recs_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                ### Observations
                - Energy recommendations **increased** as load-shedding worsened
                - Peak recommendations coincide with crisis years (2022-2023)
                - Recurring themes: maintenance, capacity expansion, renewable integration
                """)
        else:
            st.info("Correlation analysis requires both economic context and recommendations data.")
            
            # Show static correlation insights
            st.subheader("📊 Key Correlations")
            st.markdown("""
            **Load-Shedding ↔ Energy Recommendations:**
            - Years with highest load-shedding show increased energy sector recommendations
            - Focus shifts from capacity to crisis management during peak years
            
            **Unemployment ↔ Labour Recommendations:**
            - Recommendations for job creation intensify as unemployment rises
            - NEET (youth unemployment) becomes recurring theme post-2020
            
            **Fiscal Constraints ↔ Implementation:**
            - Budget recommendations frequently cite lack of implementation
            - Recurring theme: insufficient allocation vs poor execution
            """)
    
    # Footer
    st.divider()
    st.markdown("""
    ---
    **Data Sources:** Parliamentary BRRR Reports (2015-2025), Stats SA, SARB, Eskom, Wikipedia  
    **Last Updated:** December 2025  
    **Repository:** [github.com/laurencehw/brrr_recs](https://github.com/laurencehw/brrr_recs)
    """)


if __name__ == "__main__":
    main()
