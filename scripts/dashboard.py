"""
South African Economic Reform Dashboard

An evidence-based analysis of policy recommendations for accelerating 
economic growth in South Africa, drawing on 10 years of parliamentary
oversight reports.

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

# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

@st.cache_data
def load_recommendations():
    """Load BRRR recommendations - full file or sample"""
    # Try full file first
    json_path = ANALYSIS_DIR / "recommendations.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    
    # Fall back to sample (for Streamlit Cloud where full file is gitignored)
    sample_path = ANALYSIS_DIR / "recommendations_sample.json"
    if sample_path.exists():
        with open(sample_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    
    return pd.DataFrame()


@st.cache_data
def load_prioritized_recommendations():
    """Load prioritized recommendations with ROI scores"""
    path = ANALYSIS_DIR / "prioritization_summary.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@st.cache_data
def load_economic_context():
    """Load economic context with load-shedding"""
    path = ANALYSIS_DIR / "economic_context_with_loadshedding.csv"
    if path.exists():
        return pd.read_csv(path)
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
def load_nlp_analysis():
    """Load NLP analysis summary"""
    path = ANALYSIS_DIR / "nlp_analysis_summary.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@st.cache_data
def load_international_benchmark():
    """Load international benchmark data"""
    path = ANALYSIS_DIR / "international_benchmark.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@st.cache_data
def load_operation_vulindlela():
    """Load Operation Vulindlela reform data"""
    path = ANALYSIS_DIR / "operation_vulindlela.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@st.cache_data
def load_peer_data():
    """Load peer country data"""
    path = ANALYSIS_DIR / "peer_country_data.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


# =============================================================================
# QUICK WINS / HIGH-ROI RECOMMENDATIONS (hardcoded from analysis)
# =============================================================================

QUICK_WINS = [
    {
        "sector": "Energy",
        "action": "Expedite grid connection approvals for renewable IPPs",
        "impact": "Add 2-3GW capacity within 18 months",
        "feasibility": "High - regulatory change only",
        "cost": "Low - administrative",
    },
    {
        "sector": "Labour",
        "action": "Fast-track Skills Development Levy disbursements to SETAs",
        "impact": "R15bn+ sitting unspent for training",
        "feasibility": "High - Treasury approval needed",
        "cost": "Zero - funds already collected",
    },
    {
        "sector": "Finance",
        "action": "Implement consequence management for irregular expenditure",
        "impact": "R300bn+ irregular spend needs accountability",
        "feasibility": "High - existing legal framework",
        "cost": "Low - enforcement",
    },
    {
        "sector": "Infrastructure",
        "action": "Clear municipal infrastructure grant backlogs",
        "impact": "Water/sanitation for 2M+ households",
        "feasibility": "Medium - capacity constraints",
        "cost": "Medium - R50bn over 3 years",
    },
    {
        "sector": "Trade",
        "action": "Reduce port turnaround times to regional benchmarks",
        "impact": "R50bn+ export value at risk",
        "feasibility": "Medium - Transnet reform needed",
        "cost": "Medium - operational + investment",
    },
    {
        "sector": "Science & Tech",
        "action": "Accelerate broadband spectrum allocation",
        "impact": "Enable 4IR, reduce data costs 50%+",
        "feasibility": "High - ICASA decision pending",
        "cost": "Low - regulatory",
    },
]

HIGH_PRIORITY_THEMES = [
    {
        "theme": "SOE Governance Reform",
        "mentions": 126,
        "key_actions": ["Independent boards", "Clear mandates", "Performance contracts"],
        "constraint": "Political will"
    },
    {
        "theme": "Irregular Expenditure",
        "mentions": 221,
        "key_actions": ["Consequence management", "Real-time monitoring", "PFMA enforcement"],
        "constraint": "Capacity"
    },
    {
        "theme": "Vacancy Filling",
        "mentions": 246,
        "key_actions": ["Lift hiring freezes in critical posts", "Skills audit", "Retention strategy"],
        "constraint": "Fiscal space"
    },
    {
        "theme": "Procurement Reform",
        "mentions": 248,
        "key_actions": ["Central procurement", "e-Tender platform", "Supplier development"],
        "constraint": "Vested interests"
    },
]


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Header
    st.title("🇿🇦 South African Economic Reform Dashboard")
    
    # Load data
    recs_df = load_recommendations()
    econ_df = load_economic_context()
    ls_data = load_loadshedding_data()
    nlp_data = load_nlp_analysis()
    benchmark = load_international_benchmark()
    peer_df = load_peer_data()
    ov_data = load_operation_vulindlela()
    
    # Sidebar navigation
    st.sidebar.header("📊 Navigation")
    
    view = st.sidebar.radio(
        "Select View",
        [
            "🏠 Overview",
            "📋 Recommendations", 
            "📈 Economic Context",
            "⚡ Electricity Crisis",
            "🌍 International Benchmark",
            "🎯 Executive Alignment",
            "🧠 NLP Insights",
        ]
    )
    
    # ==========================================================================
    # VIEW: OVERVIEW
    # ==========================================================================
    if view == "🏠 Overview":
        render_overview(recs_df, econ_df, ls_data)
    
    # ==========================================================================
    # VIEW: RECOMMENDATIONS
    # ==========================================================================
    elif view == "📋 Recommendations":
        render_recommendations(recs_df)
    
    # ==========================================================================
    # VIEW: ECONOMIC CONTEXT
    # ==========================================================================
    elif view == "📈 Economic Context":
        render_economic_context(econ_df)
    
    # ==========================================================================
    # VIEW: ELECTRICITY CRISIS
    # ==========================================================================
    elif view == "⚡ Electricity Crisis":
        render_electricity_crisis(econ_df, ls_data, recs_df)
    
    # ==========================================================================
    # VIEW: INTERNATIONAL BENCHMARK
    # ==========================================================================
    elif view == "🌍 International Benchmark":
        render_international_benchmark(benchmark, peer_df)
    
    # ==========================================================================
    # VIEW: EXECUTIVE ALIGNMENT (Operation Vulindlela)
    # ==========================================================================
    elif view == "🎯 Executive Alignment":
        render_executive_alignment(ov_data, recs_df)
    
    # ==========================================================================
    # VIEW: NLP INSIGHTS
    # ==========================================================================
    elif view == "🧠 NLP Insights":
        render_nlp_insights(nlp_data)
    
    # Footer
    st.divider()
    st.markdown("""
    **Data Sources:** Parliamentary BRRR Reports (2015-2025), Stats SA, SARB, Eskom  
    **Repository:** [github.com/laurencehw/brrr_recs](https://github.com/laurencehw/brrr_recs)
    """)


# =============================================================================
# VIEW RENDERERS
# =============================================================================

def render_overview(recs_df, econ_df, ls_data):
    """Render the Overview page - project intro + top actions"""
    
    # Project description
    st.markdown("""
    ## The Challenge
    
    South Africa faces a **triple crisis**: 33% unemployment, a decade-long electricity shortage, 
    and mounting fiscal constraints. Yet Parliament has been generating detailed, actionable 
    recommendations for reform every year—largely unimplemented.
    
    ## What We Did
    
    We analyzed **10 years of Budget Review and Recommendation Reports (BRRRs)** from 
    parliamentary portfolio committees—the formal mechanism for legislative oversight of 
    government departments.
    
    - 📄 **50 reports** from 6 priority sectors (2015-2025)
    - 📝 **5,256 recommendations** extracted and categorized
    - 🎯 **441 Quick Wins** identified (high impact, high feasibility, low cost)
    - 📊 Enriched with economic data, load-shedding history, and peer benchmarks
    
    ## The Goal
    
    Identify **implementable reforms** that can accelerate growth within existing constraints—
    not a wish list, but a practical agenda based on what Parliament has already recommended.
    """)
    
    st.divider()
    
    # Key metrics
    st.subheader("📊 The Numbers")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Recommendations", "5,256")
    with col2:
        st.metric("Quick Wins Identified", "441")
    with col3:
        days = ls_data.get('summary', {}).get('total_days_loadshedding', 944) if ls_data else 944
        st.metric("Days of Load-Shedding", f"{days:,}")
    with col4:
        if not econ_df.empty and 'unemployment_rate' in econ_df.columns:
            unemp = econ_df['unemployment_rate'].iloc[-2]  # 2024
            st.metric("Unemployment (2024)", f"{unemp:.1f}%")
        else:
            st.metric("Unemployment (2024)", "32.9%")
    
    st.divider()
    
    # TOP RECOMMENDED ACTIONS
    st.subheader("🎯 Top Recommended Actions")
    st.markdown("*High-impact reforms that Parliament has repeatedly called for:*")
    
    for i, qw in enumerate(QUICK_WINS, 1):
        with st.expander(f"**{i}. [{qw['sector']}] {qw['action']}**", expanded=(i <= 3)):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Impact:** {qw['impact']}")
            with col2:
                st.markdown(f"**Feasibility:** {qw['feasibility']}")
            with col3:
                st.markdown(f"**Cost:** {qw['cost']}")
    
    st.divider()
    
    # RECURRING THEMES
    st.subheader("🔄 Recurring Themes Across Sectors")
    st.markdown("*Issues that appear year after year—evidence of non-implementation:*")
    
    cols = st.columns(2)
    for i, theme in enumerate(HIGH_PRIORITY_THEMES):
        with cols[i % 2]:
            st.markdown(f"**{theme['theme']}** ({theme['mentions']} mentions)")
            st.caption(f"Key actions: {', '.join(theme['key_actions'])}")
            st.caption(f"⚠️ Constraint: {theme['constraint']}")
    
    st.divider()
    
    # CONTEXT SNAPSHOT
    st.subheader("📈 Economic Context Snapshot")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **The Constraints:**
        - Debt-to-GDP: **73.7%** (vs 60% peer average)
        - GDP growth: **1.1%** (vs 4.2% peer average)  
        - Youth unemployment: **59.7%** (worst among peers)
        - Inequality (Gini): **63.0** (highest in the world)
        """)
    
    with col2:
        st.markdown("""
        **The Opportunities:**
        - R15bn+ unspent in Skills Levy
        - 90%+ renewable potential (like Kenya)
        - Mineral wealth for battery manufacturing
        - AfCFTA market access (1.3bn consumers)
        """)


def render_recommendations(recs_df):
    """Render the Recommendations explorer page"""
    
    st.header("📋 Recommendations Explorer")
    
    if recs_df.empty:
        st.warning("Recommendations data not loaded. The file may be excluded from git.")
        return
    
    # Check if this is the sample or full dataset
    total_recs = len(recs_df)
    is_sample = total_recs < 5000
    
    if is_sample:
        st.markdown(f"*Showing sample of {total_recs:,} recommendations (full dataset: 5,256)*")
        st.info("📝 This is a sample dataset for demonstration. The full 5,256 recommendations are available in the local version.")
    else:
        st.markdown("*Browse and filter 5,256 parliamentary recommendations from 2015-2025*")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sectors = ['All'] + sorted(recs_df['sector'].dropna().unique().tolist())
        selected_sector = st.selectbox("Sector", sectors)
    
    with col2:
        years = ['All'] + sorted(recs_df['year'].dropna().unique().tolist())
        selected_year = st.selectbox("Year", years)
    
    with col3:
        search = st.text_input("🔍 Search keywords")
    
    # Apply filters
    filtered = recs_df.copy()
    if selected_sector != 'All':
        filtered = filtered[filtered['sector'] == selected_sector]
    if selected_year != 'All':
        filtered = filtered[filtered['year'] == selected_year]
    if search:
        filtered = filtered[filtered['recommendation'].str.contains(search, case=False, na=False)]
    
    st.markdown(f"**Showing {len(filtered):,} of {len(recs_df):,} recommendations**")
    
    # Summary stats
    col1, col2 = st.columns(2)
    
    with col1:
        # By sector
        sector_counts = filtered['sector'].value_counts()
        fig = px.pie(values=sector_counts.values, names=sector_counts.index,
                     title="By Sector")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # By year
        year_counts = filtered['year'].value_counts().sort_index()
        fig = px.bar(x=year_counts.index, y=year_counts.values,
                     title="By Year", labels={'x': 'Year', 'y': 'Count'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("📄 Recommendations")
    display_cols = ['year', 'sector', 'category', 'recommendation']
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[available].head(200), use_container_width=True)


def render_economic_context(econ_df):
    """Render the Economic Context page"""
    
    st.header("📈 Economic Context (2015-2025)")
    st.markdown("*The macro backdrop against which recommendations were made*")
    
    if econ_df.empty:
        st.warning("Economic data not loaded.")
        return
    
    # Key indicators over time
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Unemployment Rate (%)', 'GDP Growth (%)', 
                       'Electricity Available (GWh)', 'Load-Shedding Days')
    )
    
    # Unemployment
    if 'unemployment_rate' in econ_df.columns:
        fig.add_trace(
            go.Scatter(x=econ_df['year'], y=econ_df['unemployment_rate'],
                      mode='lines+markers', name='Unemployment', 
                      line=dict(color='#e74c3c')),
            row=1, col=1
        )
    
    # GDP Growth
    if 'gdp_growth_pct' in econ_df.columns:
        colors = ['#27ae60' if g > 0 else '#e74c3c' for g in econ_df['gdp_growth_pct']]
        fig.add_trace(
            go.Bar(x=econ_df['year'], y=econ_df['gdp_growth_pct'],
                  name='GDP Growth', marker_color=colors),
            row=1, col=2
        )
    
    # Electricity
    if 'electricity_gwh' in econ_df.columns:
        fig.add_trace(
            go.Scatter(x=econ_df['year'], y=econ_df['electricity_gwh'],
                      mode='lines+markers', name='Electricity',
                      line=dict(color='#f39c12')),
            row=2, col=1
        )
    
    # Load-shedding days
    if 'days_with_loadshedding' in econ_df.columns:
        fig.add_trace(
            go.Bar(x=econ_df['year'], y=econ_df['days_with_loadshedding'],
                  name='Load-shedding Days', marker_color='#9b59b6'),
            row=2, col=2
        )
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("📊 Data Table")
    display_cols = ['year', 'unemployment_rate', 'gdp_growth_pct', 
                   'electricity_gwh', 'days_with_loadshedding', 'max_stage']
    available = [c for c in display_cols if c in econ_df.columns]
    st.dataframe(econ_df[available], use_container_width=True)
    
    # Key takeaways
    st.subheader("📝 Key Observations")
    st.markdown("""
    - **Unemployment** rose from 25% (2015) to 33%+ (2024)—9 percentage points
    - **GDP growth** averaged just 0.8% annually (vs 5%+ needed for job creation)
    - **Electricity availability** declined 11% despite demand growth
    - **Load-shedding** peaked in 2022-2023 with 200+ days per year
    - **COVID-19** caused -6.3% GDP contraction in 2020
    """)


def render_electricity_crisis(econ_df, ls_data, recs_df):
    """Render the Electricity Crisis deep-dive"""
    
    st.header("⚡ The Electricity Crisis")
    st.markdown("*A decade of load-shedding and its economic impact*")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    summary = ls_data.get('summary', {}) if ls_data else {}
    
    with col1:
        st.metric("Total Days", f"{summary.get('total_days_loadshedding', 944):,}")
    with col2:
        st.metric("Peak Year", summary.get('peak_year', '2023'))
    with col3:
        st.metric("Est. Economic Cost", f"R{summary.get('total_estimated_cost_rbillion', 2120):,.0f}bn")
    with col4:
        st.metric("First Stage 6", summary.get('first_stage_6', 'Dec 2019'))
    
    st.divider()
    
    # Timeline
    if ls_data and 'annual_data' in ls_data:
        st.subheader("📊 Load-Shedding by Year")
        
        annual = ls_data['annual_data']
        years = sorted([int(y) for y in annual.keys()])
        
        df_annual = pd.DataFrame([
            {
                'year': y,
                'days': annual[str(y)]['days_with_loadshedding'],
                'max_stage': annual[str(y)]['max_stage'],
                'severity': annual[str(y)]['severity']
            }
            for y in years
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            colors = ['#27ae60' if d < 50 else '#f39c12' if d < 150 else '#e74c3c' 
                     for d in df_annual['days']]
            fig = px.bar(df_annual, x='year', y='days', 
                        title="Days with Load-Shedding",
                        color='days',
                        color_continuous_scale='RdYlGn_r')
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(df_annual, x='year', y='max_stage',
                        title="Maximum Stage Reached",
                        color='max_stage',
                        color_continuous_scale='Reds')
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Energy recommendations correlation
    st.subheader("🔗 Parliamentary Response")
    
    if not recs_df.empty:
        energy_recs = recs_df[recs_df['sector'].str.contains('nergy', case=False, na=False)]
        by_year = energy_recs.groupby('year').size().reset_index(name='count')
        
        fig = px.bar(by_year, x='year', y='count',
                    title="Energy Sector Recommendations by Year",
                    color='count', color_continuous_scale='Oranges')
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Recurring Energy Recommendations:**
        - Accelerate independent power producer (IPP) procurement
        - Address Eskom's maintenance backlog
        - Expedite renewable energy grid connections
        - Reform electricity pricing and Nersa regulation
        - Unbundle Eskom (generation, transmission, distribution)
        """)
    
    # Economic impact
    st.subheader("💰 Economic Impact")
    st.markdown("""
    Load-shedding has cost the South African economy an estimated **R2+ trillion** since 2015:
    
    | Impact Area | Estimated Annual Cost |
    |-------------|----------------------|
    | Lost GDP | R150-200bn |
    | Business closures | Unknown (thousands) |
    | Investment deterrence | R100bn+ |
    | Unemployment | 500,000+ jobs |
    
    *Sources: Various economic analyses, Treasury estimates*
    """)


def render_international_benchmark(benchmark, peer_df):
    """Render the International Benchmark page"""
    
    st.header("🌍 International Benchmarking")
    st.markdown("*How does South Africa compare to peer emerging markets?*")
    
    if not benchmark or peer_df.empty:
        st.info("Run `python scripts/international_benchmark.py` to generate data.")
        return
    
    rankings = benchmark.get('rankings', {})
    
    # Key rankings
    st.subheader("📊 SA Rankings (out of 10 peer countries)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        r = rankings.get('unemployment_rate', {})
        st.metric("Unemployment", f"#{r.get('rank', 'N/A')}", 
                 f"{r.get('gap', 0):+.1f}% vs peers", delta_color="inverse")
    
    with col2:
        r = rankings.get('gdp_growth_2024', {})
        st.metric("GDP Growth", f"#{r.get('rank', 'N/A')}",
                 f"{r.get('gap', 0):+.1f}% vs peers")
    
    with col3:
        r = rankings.get('gini_coefficient', {})
        st.metric("Inequality", f"#{r.get('rank', 'N/A')}",
                 f"{r.get('gap', 0):+.1f} vs peers", delta_color="inverse")
    
    with col4:
        r = rankings.get('renewable_energy_pct', {})
        st.metric("Renewables", f"#{r.get('rank', 'N/A')}",
                 f"{r.get('gap', 0):+.1f}% vs peers")
    
    st.divider()
    
    # Comparative charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(peer_df.sort_values('unemployment_rate'),
                    x='unemployment_rate', y='country', orientation='h',
                    title="Unemployment Rate (%)",
                    color='unemployment_rate', color_continuous_scale='RdYlGn_r')
        fig.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(peer_df.sort_values('gdp_growth_2024'),
                    x='gdp_growth_2024', y='country', orientation='h',
                    title="GDP Growth 2024 (%)",
                    color='gdp_growth_2024', color_continuous_scale='RdYlGn')
        fig.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Reform lessons
    st.subheader("📚 Reform Lessons from Peers")
    
    lessons = benchmark.get('reform_lessons', {})
    
    cols = st.columns(3)
    for i, (country, lesson) in enumerate(lessons.items()):
        with cols[i % 3]:
            flag = {"Vietnam": "🇻🇳", "Indonesia": "🇮🇩", "India": "🇮🇳", 
                   "Kenya": "🇰🇪", "Mexico": "🇲🇽", "Brazil": "🇧🇷"}.get(country, "🌍")
            st.markdown(f"**{flag} {country}**")
            st.markdown(f"*{lesson.get('success_area', '')}*")
            st.caption(lesson.get('relevance_to_sa', ''))
    
    st.divider()
    
    # Full data
    st.subheader("📋 Full Comparison Data")
    cols = ['country', 'gdp_per_capita_usd', 'gdp_growth_2024', 'unemployment_rate',
           'youth_unemployment', 'debt_to_gdp', 'gini_coefficient', 'renewable_energy_pct']
    available = [c for c in cols if c in peer_df.columns]
    st.dataframe(peer_df[available], use_container_width=True)


def render_executive_alignment(ov_data, recs_df):
    """Render the Executive Alignment page - OV vs BRRR analysis"""
    
    st.header("🎯 Executive Alignment")
    st.markdown("*How do Executive reforms align with Parliament's recommendations?*")
    
    if not ov_data:
        st.warning("Operation Vulindlela data not loaded.")
        return
    
    # Context
    st.markdown(f"""
    ### Operation Vulindlela
    **{ov_data['metadata']['meaning']}** — a joint initiative between the Presidency and 
    National Treasury launched in {ov_data['metadata']['launch_date']} to accelerate structural 
    reforms and unlock investment.
    
    This view compares the Executive's reform priorities with Parliament's BRRR recommendations 
    to identify areas of convergence and critical gaps.
    """)
    
    st.divider()
    
    # Key Statistics
    stats = ov_data.get('key_statistics', {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total OV Reforms", stats.get('total_ov_reforms_tracked', 24))
    with col2:
        st.metric("Completed", stats.get('completed_reforms', 5))
    with col3:
        st.metric("In Progress", stats.get('in_progress_reforms', 19))
    with col4:
        st.metric("Avg Progress", f"{stats.get('average_progress_pct', 47)}%")
    
    st.divider()
    
    # Reform Progress by Priority Area
    st.subheader("📊 Reform Progress by Priority Area")
    
    # Collect reform data
    reform_data = []
    for phase in ov_data.get('phases', []):
        for area in phase.get('priority_areas', []):
            for reform in area.get('reforms', []):
                reform_data.append({
                    'Priority Area': f"{area['icon']} {area['name']}",
                    'Reform': reform['title'][:50] + ('...' if len(reform['title']) > 50 else ''),
                    'Progress': reform.get('progress_pct', 0),
                    'Status': reform.get('status', 'in_progress'),
                    'Full Title': reform['title']
                })
    
    reform_df = pd.DataFrame(reform_data)
    
    # Create grouped bar chart
    fig = px.bar(
        reform_df, 
        x='Progress', 
        y='Reform',
        color='Priority Area',
        orientation='h',
        title='Reform Progress (%)',
        hover_data=['Full Title']
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Alignment Matrix
    st.subheader("🔗 Parliament ↔ Executive Alignment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Strong Alignment")
        st.markdown("*Where OV directly addresses BRRR priorities:*")
        for item in ov_data['alignment_summary'].get('strong_alignment', []):
            st.success(f"""
            **{item['brrr_theme']}**  
            📝 {item['brrr_mentions']} BRRR mentions → 🎯 {item['ov_reforms']} OV reforms  
            {item['assessment']}
            """)
    
    with col2:
        st.markdown("### ⚡ Moderate Alignment")
        st.markdown("*Partial overlap - more could be done:*")
        for item in ov_data['alignment_summary'].get('moderate_alignment', []):
            st.warning(f"""
            **{item['brrr_theme']}**  
            📝 {item['brrr_mentions']} BRRR mentions → 🎯 {item['ov_reforms']} OV reforms  
            {item['assessment']}
            """)
    
    st.divider()
    
    # Critical Gaps
    st.subheader("🚨 Critical Gaps")
    st.markdown("*Parliament repeatedly flags these issues, but they're NOT part of Operation Vulindlela:*")
    
    gap_data = ov_data['alignment_summary'].get('gaps', [])
    cols = st.columns(2)
    for i, gap in enumerate(gap_data):
        with cols[i % 2]:
            st.error(f"""
            **{gap['brrr_theme']}**  
            📝 **{gap['brrr_mentions']}** BRRR mentions → 🎯 **0** OV reforms  
            ⚠️ {gap['assessment']}
            """)
    
    st.divider()
    
    # Visualization: Alignment Heatmap
    st.subheader("📈 Alignment Heatmap")
    
    # Build alignment data
    alignment_data = []
    for item in ov_data['alignment_summary'].get('strong_alignment', []):
        alignment_data.append({'Theme': item['brrr_theme'], 'BRRR Mentions': item['brrr_mentions'], 'OV Reforms': item['ov_reforms'], 'Type': 'Strong'})
    for item in ov_data['alignment_summary'].get('moderate_alignment', []):
        alignment_data.append({'Theme': item['brrr_theme'], 'BRRR Mentions': item['brrr_mentions'], 'OV Reforms': item['ov_reforms'], 'Type': 'Moderate'})
    for item in ov_data['alignment_summary'].get('gaps', []):
        alignment_data.append({'Theme': item['brrr_theme'], 'BRRR Mentions': item['brrr_mentions'], 'OV Reforms': item['ov_reforms'], 'Type': 'Gap'})
    
    align_df = pd.DataFrame(alignment_data)
    
    fig = px.scatter(
        align_df,
        x='BRRR Mentions',
        y='OV Reforms',
        size='BRRR Mentions',
        color='Type',
        text='Theme',
        color_discrete_map={'Strong': '#27ae60', 'Moderate': '#f39c12', 'Gap': '#e74c3c'},
        title='BRRR Mentions vs OV Reforms (size = BRRR frequency)'
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Key Insight
    st.subheader("💡 Key Insight")
    st.markdown("""
    **The data reveals a significant alignment gap:**
    
    While Operation Vulindlela addresses major structural reforms (energy, logistics, water), 
    it does **not** tackle the governance and accountability issues that Parliament raises 
    most frequently:
    
    | Issue | BRRR Mentions | OV Response |
    |-------|--------------|-------------|
    | Procurement Reform | 248 | ❌ Not addressed |
    | Vacancy Filling | 246 | ❌ Not addressed |
    | Irregular Expenditure | 221 | ❌ Not addressed |
    | Consequence Management | 156 | ❌ Not addressed |
    
    **Implication:** Structural reforms will be undermined if governance fundamentals 
    remain broken. A successful reform agenda needs BOTH infrastructure investment AND 
    public service accountability.
    
    **Recommendation:** Expand OV Phase 2 or create a parallel initiative focused on 
    public financial management and consequence management.
    """)


def render_nlp_insights(nlp_data):
    """Render the NLP Insights page"""
    
    st.header("🧠 NLP Insights")
    st.markdown("*What does the language of recommendations tell us?*")
    
    if not nlp_data:
        st.info("Run `python scripts/nlp_analysis.py` to generate NLP analysis.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = nlp_data.get('average_sentiment_score', 0)
        emoji = "😊" if score > 0.2 else "😐" if score > -0.2 else "😟"
        st.metric("Avg Sentiment", f"{score:.2f} {emoji}")
    
    with col2:
        st.metric("High Concern Items", nlp_data.get('high_concern_count', 0))
    
    with col3:
        st.metric("With Monetary Refs", nlp_data.get('recommendations_with_monetary_refs', 0))
    
    with col4:
        st.metric("Avg Word Count", f"{nlp_data.get('average_word_count', 0):.0f}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    # Sentiment distribution
    with col1:
        st.subheader("📊 Sentiment Distribution")
        sentiment = nlp_data.get('sentiment_distribution', {})
        if sentiment:
            fig = px.pie(values=list(sentiment.values()),
                        names=[s.capitalize() for s in sentiment.keys()],
                        color=list(sentiment.keys()),
                        color_discrete_map={'positive': '#27ae60', 
                                           'neutral': '#95a5a6', 
                                           'negative': '#e74c3c'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Urgency distribution
    with col2:
        st.subheader("🚨 Urgency Distribution")
        urgency = nlp_data.get('urgency_distribution', {})
        if urgency:
            fig = px.pie(values=list(urgency.values()),
                        names=[u.capitalize() for u in urgency.keys()],
                        color=list(urgency.keys()),
                        color_discrete_map={'high': '#e74c3c',
                                           'medium': '#f39c12',
                                           'low': '#27ae60'})
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Policy themes
    st.subheader("📌 Policy Themes Detected")
    themes = nlp_data.get('entity_category_frequency', {})
    if themes:
        sorted_themes = sorted(themes.items(), key=lambda x: -x[1])
        fig = px.bar(x=[t[1] for t in sorted_themes],
                    y=[t[0].replace('_', ' ').title() for t in sorted_themes],
                    orientation='h', title="Theme Frequency in Recommendations")
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, yaxis_title="")
        fig.update_traces(marker_color='#3498db')
        st.plotly_chart(fig, use_container_width=True)
    
    # Interpretation
    st.subheader("📝 Interpretation")
    st.markdown("""
    **Sentiment Analysis reveals:**
    - Most recommendations are **neutral** (factual, procedural)
    - Positive sentiment often tied to "improvement" language
    - Negative sentiment flags urgency or concern
    
    **Urgency indicators:**
    - Words like "immediate", "urgent", "critical" flagged as high urgency
    - Only ~1% of recommendations use urgent language
    - Most committees use measured, procedural tone
    
    **Policy themes:**
    - Service delivery and fiscal issues dominate
    - Governance/accountability is a cross-cutting concern
    - SOE-related mentions concentrate in energy and transport
    """)


if __name__ == "__main__":
    main()
