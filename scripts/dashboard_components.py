"""
Enhanced Dashboard Components
=============================
Reusable UI components for the BRRR Recommendations Dashboard.
Includes faceted search, pagination, export utilities, and comparison tools.
"""

import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Check optional dependencies
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'current_page': 0,
        'page_size': 50,
        'saved_searches': {},
        'comparison_items': [],
        'view_history': [],
        'preferences': {
            'theme': 'light',
            'chart_style': 'plotly',
            'export_format': 'csv'
        },
        'filters': {
            'sectors': [],
            'years': [],
            'categories': [],
            'min_roi': 0,
            'search_text': ''
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# FACETED SEARCH
# =============================================================================

def render_faceted_search(
    df: pd.DataFrame,
    key_prefix: str = "faceted"
) -> pd.DataFrame:
    """
    Render a multi-dimensional faceted search interface.

    Args:
        df: DataFrame to filter
        key_prefix: Unique prefix for widget keys

    Returns:
        Filtered DataFrame
    """
    st.subheader("🔎 Advanced Filters")

    # Get unique values for filters
    sectors = ['All'] + sorted(df['sector'].dropna().unique().tolist()) if 'sector' in df.columns else ['All']
    years = sorted(df['year'].dropna().unique().tolist()) if 'year' in df.columns else []
    categories = ['All'] + sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else ['All']

    # Filter layout
    col1, col2 = st.columns(2)

    with col1:
        selected_sectors = st.multiselect(
            "Sectors",
            options=sectors[1:],  # Exclude 'All'
            default=[],
            key=f"{key_prefix}_sectors",
            help="Filter by one or more sectors"
        )

        if years:
            year_range = st.slider(
                "Year Range",
                min_value=int(min(years)),
                max_value=int(max(years)),
                value=(int(min(years)), int(max(years))),
                key=f"{key_prefix}_years"
            )
        else:
            year_range = None

    with col2:
        selected_categories = st.multiselect(
            "Categories",
            options=categories[1:],  # Exclude 'All'
            default=[],
            key=f"{key_prefix}_categories",
            help="Filter by one or more categories"
        )

        # Score filters if available
        if 'roi_score' in df.columns:
            min_roi = st.slider(
                "Minimum ROI Score",
                min_value=0,
                max_value=10,
                value=0,
                key=f"{key_prefix}_roi"
            )
        else:
            min_roi = 0

    # Text search
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_text = st.text_input(
            "🔍 Keyword Search",
            placeholder="Enter keywords (e.g., 'procurement irregular expenditure')",
            key=f"{key_prefix}_search"
        )
    with search_col2:
        search_mode = st.selectbox(
            "Mode",
            ["All words (AND)", "Any word (OR)"],
            key=f"{key_prefix}_search_mode"
        )

    # Apply filters
    filtered = df.copy()

    if selected_sectors:
        filtered = filtered[filtered['sector'].isin(selected_sectors)]

    if year_range and 'year' in filtered.columns:
        filtered = filtered[(filtered['year'] >= year_range[0]) & (filtered['year'] <= year_range[1])]

    if selected_categories:
        filtered = filtered[filtered['category'].isin(selected_categories)]

    if min_roi > 0 and 'roi_score' in filtered.columns:
        filtered = filtered[filtered['roi_score'] >= min_roi]

    if search_text:
        words = search_text.lower().split()
        if 'recommendation' in filtered.columns:
            if search_mode == "All words (AND)":
                mask = filtered['recommendation'].str.lower().apply(
                    lambda x: all(w in str(x) for w in words) if pd.notna(x) else False
                )
            else:
                mask = filtered['recommendation'].str.lower().apply(
                    lambda x: any(w in str(x) for w in words) if pd.notna(x) else False
                )
            filtered = filtered[mask]

    # Store current filters
    st.session_state['filters'] = {
        'sectors': selected_sectors,
        'years': year_range,
        'categories': selected_categories,
        'min_roi': min_roi,
        'search_text': search_text
    }

    # Results summary
    st.markdown(f"**Found {len(filtered):,} of {len(df):,} recommendations**")

    # Save search option
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        save_name = st.text_input("Save as", placeholder="My search", key=f"{key_prefix}_save_name", label_visibility="collapsed")
    with col3:
        if st.button("💾 Save Search", key=f"{key_prefix}_save_btn"):
            if save_name:
                st.session_state['saved_searches'][save_name] = st.session_state['filters'].copy()
                st.success(f"Saved as '{save_name}'")

    # Load saved search
    if st.session_state['saved_searches']:
        with col1:
            saved_options = ['Load saved search...'] + list(st.session_state['saved_searches'].keys())
            selected_saved = st.selectbox(
                "Load",
                saved_options,
                key=f"{key_prefix}_load_saved",
                label_visibility="collapsed"
            )
            if selected_saved != 'Load saved search...':
                st.info(f"Applied filters from '{selected_saved}'")

    return filtered


# =============================================================================
# PAGINATION
# =============================================================================

def render_paginated_dataframe(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    page_size: int = 50,
    key_prefix: str = "paginated"
) -> None:
    """
    Render a paginated dataframe with navigation controls.

    Args:
        df: DataFrame to display
        columns: Columns to show (None for all)
        page_size: Rows per page
        key_prefix: Unique prefix for widget keys
    """
    if df.empty:
        st.info("No data to display")
        return

    # Determine columns to display
    if columns:
        display_cols = [c for c in columns if c in df.columns]
    else:
        display_cols = df.columns.tolist()

    # Calculate pagination
    total_rows = len(df)
    total_pages = (total_rows - 1) // page_size + 1

    # Ensure current page is valid
    if f'{key_prefix}_page' not in st.session_state:
        st.session_state[f'{key_prefix}_page'] = 0

    current_page = st.session_state[f'{key_prefix}_page']
    current_page = min(current_page, total_pages - 1)
    current_page = max(current_page, 0)

    # Navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First", key=f"{key_prefix}_first", disabled=current_page == 0):
            st.session_state[f'{key_prefix}_page'] = 0
            st.rerun()

    with col2:
        if st.button("◀️ Prev", key=f"{key_prefix}_prev", disabled=current_page == 0):
            st.session_state[f'{key_prefix}_page'] = current_page - 1
            st.rerun()

    with col3:
        st.markdown(f"<div style='text-align: center'>Page **{current_page + 1}** of **{total_pages}** ({total_rows:,} rows)</div>", unsafe_allow_html=True)

    with col4:
        if st.button("Next ▶️", key=f"{key_prefix}_next", disabled=current_page >= total_pages - 1):
            st.session_state[f'{key_prefix}_page'] = current_page + 1
            st.rerun()

    with col5:
        if st.button("Last ⏭️", key=f"{key_prefix}_last", disabled=current_page >= total_pages - 1):
            st.session_state[f'{key_prefix}_page'] = total_pages - 1
            st.rerun()

    # Calculate slice
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_rows)

    # Display data
    st.dataframe(
        df.iloc[start_idx:end_idx][display_cols],
        use_container_width=True,
        height=min(600, (end_idx - start_idx + 1) * 35 + 38)
    )

    # Page size selector
    col1, col2 = st.columns([3, 1])
    with col2:
        new_page_size = st.selectbox(
            "Rows per page",
            [25, 50, 100, 200],
            index=[25, 50, 100, 200].index(page_size) if page_size in [25, 50, 100, 200] else 1,
            key=f"{key_prefix}_page_size"
        )


# =============================================================================
# EXPORT UTILITIES
# =============================================================================

def render_export_options(
    df: pd.DataFrame,
    filename_prefix: str = "export",
    key_prefix: str = "export"
) -> None:
    """
    Render comprehensive export options including CSV, Excel, PDF, and JSON.

    Args:
        df: DataFrame to export
        filename_prefix: Prefix for exported files
        key_prefix: Unique prefix for widget keys
    """
    st.subheader("📥 Export Options")

    col1, col2, col3, col4 = st.columns(4)

    # CSV Export
    with col1:
        st.markdown("**CSV**")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Download CSV",
            csv_data,
            f"{filename_prefix}.csv",
            "text/csv",
            key=f"{key_prefix}_csv"
        )

    # Excel Export
    with col2:
        st.markdown("**Excel**")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        excel_data = excel_buffer.getvalue()
        st.download_button(
            "⬇️ Download Excel",
            excel_data,
            f"{filename_prefix}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_excel"
        )

    # JSON Export
    with col3:
        st.markdown("**JSON**")
        json_data = df.to_json(orient='records', indent=2).encode('utf-8')
        st.download_button(
            "⬇️ Download JSON",
            json_data,
            f"{filename_prefix}.json",
            "application/json",
            key=f"{key_prefix}_json"
        )

    # PDF Export (if available)
    with col4:
        st.markdown("**PDF Report**")
        if FPDF_AVAILABLE:
            if st.button("📄 Generate PDF", key=f"{key_prefix}_pdf_btn"):
                pdf_data = generate_pdf_report(df, filename_prefix)
                st.download_button(
                    "⬇️ Download PDF",
                    pdf_data,
                    f"{filename_prefix}.pdf",
                    "application/pdf",
                    key=f"{key_prefix}_pdf"
                )
        else:
            st.caption("Install fpdf2 for PDF export")


def generate_pdf_report(df: pd.DataFrame, title: str = "Report") -> bytes:
    """Generate a PDF report from DataFrame."""
    if not FPDF_AVAILABLE:
        return b""

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(5)

    # Metadata
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 8, f"Total Records: {len(df):,}", ln=True)
    pdf.ln(5)

    # Summary statistics
    if 'sector' in df.columns:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, "By Sector:", ln=True)
        pdf.set_font('Helvetica', '', 10)
        for sector, count in df['sector'].value_counts().head(10).items():
            pdf.cell(0, 6, f"  - {sector}: {count}", ln=True)
        pdf.ln(5)

    if 'year' in df.columns:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, "By Year:", ln=True)
        pdf.set_font('Helvetica', '', 10)
        for year, count in df['year'].value_counts().sort_index().items():
            pdf.cell(0, 6, f"  - {year}: {count}", ln=True)

    return pdf.output()


# =============================================================================
# COMPARISON TOOLS
# =============================================================================

def render_comparison_view(
    df: pd.DataFrame,
    id_column: str = 'id',
    key_prefix: str = "compare"
) -> None:
    """
    Render a side-by-side comparison interface for recommendations.

    Args:
        df: DataFrame with recommendations
        id_column: Column to use as identifier
        key_prefix: Unique prefix for widget keys
    """
    st.subheader("🔄 Compare Recommendations")

    if df.empty:
        st.info("No data available for comparison")
        return

    # Create selection options
    if id_column in df.columns:
        options = df[id_column].tolist()
    else:
        options = df.index.tolist()

    # Selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**First Recommendation**")
        item1_idx = st.selectbox(
            "Select first item",
            range(len(df)),
            format_func=lambda i: f"{df.iloc[i].get('year', 'N/A')} - {str(df.iloc[i].get('recommendation', ''))[:50]}...",
            key=f"{key_prefix}_item1"
        )

    with col2:
        st.markdown("**Second Recommendation**")
        item2_idx = st.selectbox(
            "Select second item",
            range(len(df)),
            format_func=lambda i: f"{df.iloc[i].get('year', 'N/A')} - {str(df.iloc[i].get('recommendation', ''))[:50]}...",
            key=f"{key_prefix}_item2"
        )

    # Display comparison
    if item1_idx is not None and item2_idx is not None:
        rec1 = df.iloc[item1_idx]
        rec2 = df.iloc[item2_idx]

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            render_recommendation_card(rec1, "Recommendation 1")

        with col2:
            render_recommendation_card(rec2, "Recommendation 2")

        # Comparison table
        st.divider()
        st.markdown("**📊 Attribute Comparison**")

        compare_cols = ['sector', 'year', 'category']
        if 'feasibility' in df.columns:
            compare_cols.append('feasibility')
        if 'impact' in df.columns:
            compare_cols.append('impact')
        if 'roi_score' in df.columns:
            compare_cols.append('roi_score')

        comparison_data = []
        for col in compare_cols:
            if col in df.columns:
                comparison_data.append({
                    'Attribute': col.replace('_', ' ').title(),
                    'Recommendation 1': rec1.get(col, 'N/A'),
                    'Recommendation 2': rec2.get(col, 'N/A'),
                    'Match': '✅' if rec1.get(col) == rec2.get(col) else '❌'
                })

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)


def render_recommendation_card(rec: pd.Series, title: str = "Recommendation") -> None:
    """Render a recommendation as a styled card."""
    st.markdown(f"### {title}")

    # Metadata badges
    badges = []
    if 'sector' in rec and pd.notna(rec['sector']):
        badges.append(f"**{rec['sector']}**")
    if 'year' in rec and pd.notna(rec['year']):
        badges.append(f"📅 {rec['year']}")
    if 'category' in rec and pd.notna(rec['category']):
        badges.append(f"📁 {rec['category']}")

    if badges:
        st.markdown(" | ".join(badges))

    # Recommendation text
    if 'recommendation' in rec and pd.notna(rec['recommendation']):
        st.markdown(f"> {rec['recommendation']}")

    # Scores if available
    score_cols = ['feasibility', 'impact', 'cost', 'roi_score']
    scores = {col: rec.get(col) for col in score_cols if col in rec and pd.notna(rec.get(col))}

    if scores:
        st.markdown("**Scores:**")
        score_text = " | ".join([f"{k.title()}: {v}" for k, v in scores.items()])
        st.caption(score_text)


# =============================================================================
# NETWORK VISUALIZATION
# =============================================================================

def render_network_analysis(
    df: pd.DataFrame,
    key_prefix: str = "network"
) -> None:
    """
    Render network analysis visualization showing recommendation relationships.

    Args:
        df: DataFrame with recommendations
        key_prefix: Unique prefix for widget keys
    """
    st.subheader("🕸️ Recommendation Network")

    if not NETWORKX_AVAILABLE:
        st.warning("Install networkx for network analysis: `pip install networkx`")
        return

    if not PLOTLY_AVAILABLE:
        st.warning("Plotly required for network visualization")
        return

    if df.empty:
        st.info("No data available")
        return

    # Build network by sector-category relationships
    G = nx.Graph()

    # Add sector nodes
    if 'sector' in df.columns:
        sectors = df['sector'].dropna().unique()
        for sector in sectors:
            G.add_node(sector, node_type='sector', size=20)

    # Add category nodes and edges
    if 'category' in df.columns and 'sector' in df.columns:
        for _, row in df.iterrows():
            sector = row.get('sector')
            category = row.get('category')
            if pd.notna(sector) and pd.notna(category):
                if category not in G.nodes():
                    G.add_node(category, node_type='category', size=10)

                # Add or strengthen edge
                if G.has_edge(sector, category):
                    G[sector][category]['weight'] += 1
                else:
                    G.add_edge(sector, category, weight=1)

    # Create layout
    pos = nx.spring_layout(G, seed=42, k=2)

    # Create Plotly figure
    edge_traces = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        weight = edge[2].get('weight', 1)
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=min(weight / 10, 5), color='#888'),
                hoverinfo='none'
            )
        )

    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []

    for node in G.nodes(data=True):
        x, y = pos[node[0]]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node[0])
        node_size.append(node[1].get('size', 15))
        node_color.append('#3498db' if node[1].get('node_type') == 'sector' else '#95a5a6')

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition='top center',
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color='white')
        )
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Network stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", len(G.nodes()))
    with col2:
        st.metric("Connections", len(G.edges()))
    with col3:
        if len(G.nodes()) > 0:
            density = nx.density(G)
            st.metric("Density", f"{density:.3f}")


# =============================================================================
# ACCESSIBILITY HELPERS
# =============================================================================

def render_accessibility_controls(key_prefix: str = "a11y") -> Dict:
    """Render accessibility control panel."""
    with st.sidebar.expander("♿ Accessibility"):
        high_contrast = st.checkbox(
            "High Contrast Mode",
            key=f"{key_prefix}_contrast"
        )

        font_size = st.select_slider(
            "Text Size",
            options=['Small', 'Normal', 'Large', 'Extra Large'],
            value='Normal',
            key=f"{key_prefix}_fontsize"
        )

        reduce_motion = st.checkbox(
            "Reduce Motion",
            key=f"{key_prefix}_motion"
        )

    return {
        'high_contrast': high_contrast,
        'font_size': font_size,
        'reduce_motion': reduce_motion
    }


def apply_accessibility_styles(settings: Dict) -> None:
    """Apply accessibility CSS based on settings."""
    css = ""

    if settings.get('high_contrast'):
        css += """
        <style>
        .stApp { background-color: #000 !important; color: #fff !important; }
        .stMarkdown { color: #fff !important; }
        .stMetric { border: 2px solid #fff !important; }
        </style>
        """

    font_sizes = {
        'Small': '14px',
        'Normal': '16px',
        'Large': '18px',
        'Extra Large': '20px'
    }
    if settings.get('font_size') in font_sizes:
        css += f"""
        <style>
        .stMarkdown p, .stText {{ font-size: {font_sizes[settings['font_size']]} !important; }}
        </style>
        """

    if css:
        st.markdown(css, unsafe_allow_html=True)


def add_chart_description(fig: Any, description: str) -> None:
    """Add accessible description for a chart."""
    with st.expander("📖 Chart Description (for screen readers)"):
        st.write(description)


# =============================================================================
# DATA STATUS INDICATOR
# =============================================================================

def render_data_status(df: pd.DataFrame, data_name: str = "data") -> None:
    """Show data freshness and status information."""
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📊 **Data Status**")
    st.sidebar.caption(f"Records: {len(df):,}")

    if 'year' in df.columns:
        years = df['year'].dropna()
        if len(years) > 0:
            st.sidebar.caption(f"Years: {int(years.min())}-{int(years.max())}")

    if 'sector' in df.columns:
        st.sidebar.caption(f"Sectors: {df['sector'].nunique()}")
