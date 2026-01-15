# Codebase Review: Analytical & UI Improvement Recommendations

**Date:** January 2026
**Reviewer:** Claude Code
**Project:** South African Economic Reform Dashboard (BRRR Analysis)

---

## Executive Summary

This codebase is a well-structured policy analysis platform that processes 5,256 parliamentary recommendations from 10 years of Budget Review and Recommendation Reports (BRRR). The current implementation includes:

- PDF text extraction and recommendation parsing
- Multi-dimensional scoring (Feasibility, Impact, Cost, ROI)
- NLP analysis (sentiment, urgency, entity extraction)
- Interactive Streamlit dashboard with 12 views
- REST API for programmatic access

The following recommendations aim to enhance both the analytical depth and user experience of the platform.

---

## Part 1: Analytical Improvements

### 1.1 Enhanced NLP with Modern Techniques

**Current State:** Rule-based sentiment analysis using keyword matching (`nlp_analysis.py:84-122`)

**Recommendations:**

#### A. Add spaCy for Entity Recognition
```python
# Instead of keyword matching, use named entity recognition
import spacy
nlp = spacy.load("en_core_web_sm")

def extract_entities_spacy(text):
    doc = nlp(text)
    entities = {
        'organizations': [ent.text for ent in doc.ents if ent.label_ == 'ORG'],
        'monetary': [ent.text for ent in doc.ents if ent.label_ == 'MONEY'],
        'dates': [ent.text for ent in doc.ents if ent.label_ == 'DATE'],
        'percentages': [ent.text for ent in doc.ents if ent.label_ == 'PERCENT'],
    }
    return entities
```

#### B. Topic Modeling with BERTopic
```python
from bertopic import BERTopic

# Discover latent topics in recommendations
topic_model = BERTopic(language="english", nr_topics=20)
topics, probs = topic_model.fit_transform(recommendations_text)

# Better than manual categorization - discovers themes automatically
```

#### C. Semantic Similarity for Deduplication
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(recommendations)

# Find duplicate/similar recommendations across years
from sklearn.metrics.pairwise import cosine_similarity
similarity_matrix = cosine_similarity(embeddings)
```

**Impact:** More accurate categorization, automatic topic discovery, better deduplication of recurring recommendations.

---

### 1.2 Implementation Status Tracking

**Current Gap:** No tracking of which recommendations were actually implemented.

**Recommendation:** Add an implementation tracking system:

```python
# New file: scripts/track_implementation.py

IMPLEMENTATION_STATUS = {
    'implemented': [],      # Fully done
    'partial': [],          # In progress
    'not_implemented': [],  # No action
    'no_longer_relevant': [] # Superseded/obsolete
}

def cross_reference_with_legislation():
    """Match recommendations to gazette announcements, bills passed"""
    pass

def cross_reference_with_budgets():
    """Track if recommended allocations appeared in subsequent budgets"""
    pass
```

**Data Sources to Integrate:**
- Government Gazette (regulations passed)
- National Treasury budget documents
- Department annual reports
- Auditor-General findings

---

### 1.3 Enhanced Scoring Framework

**Current State:** Rule-based scoring (`prioritize_recommendations.py`) with hardcoded weights.

**Recommendations:**

#### A. Add Evidence-Based Weighting
```python
# Instead of static weights, derive from historical outcomes
def calculate_evidence_weight(rec_type, historical_success_rate):
    """Weight scoring by what has worked before"""
    base_weight = {
        'legislative_change': 0.3,  # Harder to implement
        'administrative': 0.8,      # Easier to implement
        'funding_allocation': 0.5,  # Depends on fiscal space
    }
    return base_weight.get(rec_type, 0.5) * historical_success_rate
```

#### B. Add Political Feasibility Score
```python
def calculate_political_feasibility(recommendation):
    """Score based on political economy factors"""
    factors = {
        'requires_legislation': -0.3,
        'inter_departmental': -0.2,  # Multiple departments = harder
        'executive_alignment': +0.4, # Aligned with OV priorities
        'public_support': +0.2,      # Popular reforms easier
        'special_interests': -0.3,   # Vested interests oppose
    }
    # Parse text for indicators and sum factors
```

#### C. Add Dependency Mapping
```python
def map_dependencies(recommendations):
    """Identify which reforms must precede others"""
    dependency_graph = {}
    # E.g., "unbundle Eskom" requires "pass Electricity Amendment Bill"
    # Use NLP to identify prerequisite language
```

---

### 1.4 Correlation Analysis

**Current Gap:** No analysis of relationships between recommendations and outcomes.

**Recommendation:** Add outcome correlation analysis:

```python
# New file: scripts/correlation_analysis.py

def correlate_with_economic_indicators():
    """
    Track if sectors with more recommendations saw better outcomes
    """
    return {
        'energy_recs_vs_loadshedding': calculate_correlation(
            energy_rec_counts_by_year,
            loadshedding_days_by_year
        ),
        'finance_recs_vs_irregular_exp': calculate_correlation(
            finance_rec_counts,
            irregular_expenditure_trends
        ),
    }

def identify_leading_indicators():
    """Which types of recommendations precede improvements?"""
    pass
```

---

### 1.5 Predictive Analytics

**Recommendation:** Add ML models to predict implementation likelihood:

```python
# New file: scripts/predict_implementation.py

from sklearn.ensemble import RandomForestClassifier

def predict_implementation_probability(recommendation):
    """
    Features:
    - Recommendation specificity (vague vs concrete)
    - Cost estimate presence
    - Deadline specified
    - Number of times repeated
    - Sector track record
    - Political alignment
    """
    features = extract_features(recommendation)
    model = load_trained_model()
    probability = model.predict_proba([features])[0][1]
    return probability
```

**Training Data:** Use historical recommendations + outcomes (manual labeling required initially).

---

### 1.6 Network Analysis

**Recommendation:** Visualize recommendation relationships:

```python
import networkx as nx

def build_recommendation_network(recommendations):
    """Create graph of connected recommendations"""
    G = nx.Graph()

    # Nodes = recommendations
    # Edges = semantic similarity > threshold

    for i, rec1 in enumerate(recommendations):
        for j, rec2 in enumerate(recommendations):
            if i < j:
                similarity = calculate_similarity(rec1, rec2)
                if similarity > 0.7:
                    G.add_edge(i, j, weight=similarity)

    # Identify clusters of related recommendations
    communities = nx.community.louvain_communities(G)
    return G, communities
```

**Dashboard Integration:** Add network visualization view showing recommendation clusters.

---

### 1.7 Fiscal Impact Modeling

**Current Gap:** Cost estimates are static (`advanced_analysis.py:231-322`).

**Recommendation:** Add dynamic fiscal modeling:

```python
def model_fiscal_impact(reform, fiscal_context):
    """
    Calculate actual budget impact considering:
    - Current fiscal space
    - Debt sustainability
    - Revenue projections
    - Competing priorities
    """
    available_fiscal_space = calculate_fiscal_space(fiscal_context)
    reform_cost = estimate_reform_cost(reform)

    return {
        'can_fund': reform_cost <= available_fiscal_space,
        'funding_gap': max(0, reform_cost - available_fiscal_space),
        'debt_impact': calculate_debt_impact(reform_cost),
        'opportunity_cost': identify_tradeoffs(reform_cost),
    }
```

---

### 1.8 Comparative Analysis Enhancements

**Current State:** International benchmarks are static (`international_benchmark.py`).

**Recommendations:**

```python
def add_dynamic_benchmarking():
    """Pull live data from World Bank/IMF APIs"""
    import wbdata

    indicators = {
        'SL.UEM.TOTL.ZS': 'unemployment',
        'NY.GDP.MKTP.KD.ZG': 'gdp_growth',
    }

    peer_countries = ['ZAF', 'BRA', 'IND', 'VNM', 'KEN']
    data = wbdata.get_dataframe(indicators, country=peer_countries)
    return data

def add_reform_success_benchmarks():
    """Compare SA reforms to successful peer reforms"""
    # E.g., Vietnam's electricity sector reforms
    # Kenya's mobile money success
    # Indonesia's fuel subsidy reform
```

---

## Part 2: UI/UX Improvements

### 2.1 Performance Optimization

**Current Issue:** All data loaded at startup (`dashboard.py:36-163`).

**Recommendations:**

#### A. Lazy Loading
```python
# Only load data when view is selected
def render_view(view_name):
    if view_name == "📋 Recommendations":
        # Load only when needed
        recs_df = load_recommendations()
        render_recommendations(recs_df)
```

#### B. Add Progress Indicators
```python
# Show loading state for expensive operations
with st.spinner('Loading 5,256 recommendations...'):
    recs_df = load_recommendations()

# Add progress bar for batch operations
progress_bar = st.progress(0)
for i, rec in enumerate(recommendations):
    process_recommendation(rec)
    progress_bar.progress((i + 1) / len(recommendations))
```

#### C. Implement Pagination
```python
# Current: st.dataframe(filtered[available].head(200))
# Better: Full pagination with state management

def paginated_dataframe(df, page_size=50):
    total_pages = len(df) // page_size + 1

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button('Previous'):
            st.session_state.page = max(0, st.session_state.page - 1)
    with col2:
        st.write(f"Page {st.session_state.page + 1} of {total_pages}")
    with col3:
        if st.button('Next'):
            st.session_state.page = min(total_pages - 1, st.session_state.page + 1)

    start = st.session_state.page * page_size
    end = start + page_size
    st.dataframe(df.iloc[start:end])
```

---

### 2.2 Enhanced Navigation

**Current State:** Single radio button sidebar (`dashboard.py:267-283`).

**Recommendations:**

#### A. Add Breadcrumbs
```python
def render_breadcrumbs(current_view):
    """Show navigation path"""
    st.markdown(f"📊 Dashboard > {current_view}")
```

#### B. Add Quick Actions Panel
```python
def render_quick_actions():
    """Floating action panel for common tasks"""
    with st.sidebar:
        st.subheader("Quick Actions")
        if st.button("🔍 Search All"):
            st.session_state.view = "🔍 Search & Export"
        if st.button("📥 Export Data"):
            export_all_data()
        if st.button("📝 Generate Brief"):
            st.session_state.view = "📝 Policy Briefs"
```

#### C. Add View History
```python
# Track and allow quick return to recent views
if 'view_history' not in st.session_state:
    st.session_state.view_history = []

def update_view_history(view):
    history = st.session_state.view_history
    if view not in history[-3:]:  # Keep last 3
        history.append(view)
    st.session_state.view_history = history[-5:]

# Display recent views
st.sidebar.markdown("**Recent:**")
for view in reversed(st.session_state.view_history[-3:]):
    if st.sidebar.button(view, key=f"recent_{view}"):
        st.session_state.current_view = view
```

---

### 2.3 Advanced Filtering & Search

**Current State:** Basic text search (`dashboard.py:541-580`).

**Recommendations:**

#### A. Faceted Search
```python
def render_faceted_search(recs_df):
    """Multi-dimensional filtering"""

    st.subheader("🔎 Advanced Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sectors = st.multiselect("Sectors", recs_df['sector'].unique())

    with col2:
        years = st.slider("Year Range", 2015, 2025, (2015, 2025))

    with col3:
        categories = st.multiselect("Categories", recs_df['category'].unique())

    with col4:
        min_roi = st.slider("Min ROI Score", 0, 10, 0)

    # Apply all filters
    filtered = recs_df.copy()
    if sectors:
        filtered = filtered[filtered['sector'].isin(sectors)]
    if years:
        filtered = filtered[(filtered['year'] >= years[0]) & (filtered['year'] <= years[1])]
    if categories:
        filtered = filtered[filtered['category'].isin(categories)]

    return filtered
```

#### B. Saved Searches
```python
def save_search(name, filters):
    """Allow users to save filter combinations"""
    if 'saved_searches' not in st.session_state:
        st.session_state.saved_searches = {}

    st.session_state.saved_searches[name] = filters

def render_saved_searches():
    """Dropdown to quickly apply saved searches"""
    saved = st.session_state.get('saved_searches', {})
    if saved:
        selected = st.selectbox("Load saved search", ['None'] + list(saved.keys()))
        if selected != 'None':
            return saved[selected]
    return None
```

#### C. Natural Language Search
```python
def natural_language_search(query, recs_df):
    """
    Allow queries like:
    - "high impact energy recommendations from 2023"
    - "quick wins for unemployment"
    - "urgent infrastructure reforms"
    """
    # Parse intent
    if 'quick win' in query.lower():
        return recs_df[
            (recs_df['feasibility'] >= 4) &
            (recs_df['impact'] >= 4) &
            (recs_df['cost'] >= 4)
        ]
    # ... more patterns
```

---

### 2.4 Improved Data Visualization

**Current State:** Basic Plotly charts (`dashboard.py` various).

**Recommendations:**

#### A. Add Interactive Drill-Down
```python
def render_interactive_treemap():
    """Drill-down from sector → category → recommendations"""
    fig = px.treemap(
        recs_df,
        path=['sector', 'category'],
        values='count',
        color='avg_roi',
        hover_data=['top_recommendation'],
        color_continuous_scale='RdYlGn'
    )

    # Click to filter
    selected = plotly_events(fig)
    if selected:
        st.session_state.filters = {'sector': selected['sector']}
```

#### B. Add Sankey Diagram for Flows
```python
def render_recommendation_flow():
    """Show flow: Sector → Category → Implementation Status"""
    import plotly.graph_objects as go

    fig = go.Figure(go.Sankey(
        node=dict(
            label=sectors + categories + statuses,
            color=color_palette
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=counts
        )
    ))
    st.plotly_chart(fig)
```

#### C. Add Sparklines in Tables
```python
def render_sector_table_with_sparklines():
    """Show trend lines inline with metrics"""
    for sector in sectors:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

        with col1:
            st.write(sector)
        with col2:
            st.metric("Total", sector_counts[sector])
        with col3:
            st.metric("ROI", f"{sector_roi[sector]:.1f}")
        with col4:
            # Mini trend chart
            fig = px.line(
                sector_by_year[sector],
                height=50,
                # Remove axes for sparkline effect
            )
            fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
```

---

### 2.5 Add Comparison Tools

**Recommendation:** Allow side-by-side comparison of recommendations:

```python
def render_comparison_view():
    """Compare two recommendations or sectors"""
    st.header("🔄 Compare")

    col1, col2 = st.columns(2)

    with col1:
        rec1 = st.selectbox("Select first recommendation", recs_df['id'])
        render_recommendation_card(rec1)

    with col2:
        rec2 = st.selectbox("Select second recommendation", recs_df['id'])
        render_recommendation_card(rec2)

    # Show differences
    st.subheader("📊 Comparison")
    comparison_df = pd.DataFrame({
        'Metric': ['Sector', 'Year', 'Impact', 'Feasibility', 'Cost', 'ROI'],
        'Recommendation 1': [rec1['sector'], rec1['year'], ...],
        'Recommendation 2': [rec2['sector'], rec2['year'], ...],
    })
    st.dataframe(comparison_df)
```

---

### 2.6 Accessibility Improvements

**Recommendations:**

#### A. Add Keyboard Navigation
```python
# Use streamlit-shortcuts or custom JS
def add_keyboard_shortcuts():
    st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 's' && e.ctrlKey) {
            // Trigger search
        }
        if (e.key === 'e' && e.ctrlKey) {
            // Trigger export
        }
    });
    </script>
    """, unsafe_allow_html=True)
```

#### B. Add High Contrast Mode
```python
def apply_accessibility_theme():
    if st.session_state.get('high_contrast', False):
        st.markdown("""
        <style>
        .stApp { background-color: #000 !important; color: #fff !important; }
        .stMetric { border: 2px solid #fff !important; }
        </style>
        """, unsafe_allow_html=True)
```

#### C. Add Screen Reader Support
```python
def accessible_chart(fig, description):
    """Add alt-text for charts"""
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Chart description (for screen readers)"):
        st.write(description)
```

---

### 2.7 Export Enhancements

**Current State:** CSV export only (`dashboard.py:586-626`).

**Recommendations:**

```python
def enhanced_export():
    """Multiple export formats"""

    st.subheader("📥 Export Options")

    format_choice = st.selectbox(
        "Format",
        ["CSV", "Excel (with formatting)", "JSON", "PDF Report", "PowerPoint"]
    )

    if format_choice == "Excel (with formatting)":
        # Create styled Excel with conditional formatting
        from openpyxl.styles import PatternFill
        # Apply colors based on ROI scores, etc.

    elif format_choice == "PDF Report":
        # Generate formatted PDF
        from fpdf import FPDF

    elif format_choice == "PowerPoint":
        # Generate presentation
        from pptx import Presentation
```

---

### 2.8 Add User Preferences/Persistence

**Recommendation:** Store user preferences across sessions:

```python
def init_user_preferences():
    """Load preferences from cookies/localStorage"""
    if 'preferences' not in st.session_state:
        st.session_state.preferences = {
            'default_view': '🏠 Overview',
            'chart_theme': 'plotly',
            'rows_per_page': 50,
            'default_sector': 'All',
            'export_format': 'CSV',
        }

def render_settings():
    """Settings panel"""
    with st.sidebar.expander("⚙️ Settings"):
        st.session_state.preferences['rows_per_page'] = st.slider(
            "Rows per page", 10, 100, 50
        )
        st.session_state.preferences['chart_theme'] = st.selectbox(
            "Chart theme", ['plotly', 'ggplot2', 'seaborn']
        )
```

---

### 2.9 Add Real-Time Updates Indicator

**Recommendation:** Show data freshness and update status:

```python
def render_data_status():
    """Show when data was last updated"""
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📊 Data updated: {get_last_update_date()}")
    st.sidebar.caption(f"📝 {len(recs_df):,} recommendations loaded")

    if data_is_stale():
        st.sidebar.warning("⚠️ Data may be outdated. Run update scripts.")
```

---

### 2.10 Mobile Responsiveness

**Recommendation:** Add responsive layouts:

```python
def get_device_type():
    """Detect mobile vs desktop"""
    # Use streamlit-javascript or user-agent
    return 'mobile' if st.session_state.get('is_mobile') else 'desktop'

def render_responsive_layout(content_func):
    """Adjust layout for device"""
    if get_device_type() == 'mobile':
        # Single column layout
        content_func(columns=1)
    else:
        # Multi-column layout
        content_func(columns=4)
```

---

## Part 3: Additional Feature Recommendations

### 3.1 Alert/Notification System

```python
def check_for_alerts():
    """Generate alerts for notable patterns"""
    alerts = []

    # Rising urgency
    if urgency_trend > 0.2:
        alerts.append("⚠️ Urgency in recommendations is increasing")

    # Unaddressed recurring issues
    recurring = get_recurring_unaddressed()
    if recurring:
        alerts.append(f"🔄 {len(recurring)} issues repeated 3+ years without action")

    # Deadline approaching
    deadline_recs = get_recommendations_with_deadlines()
    for rec in deadline_recs:
        if rec['deadline'] < datetime.now() + timedelta(days=90):
            alerts.append(f"⏰ Deadline approaching: {rec['title']}")

    return alerts

# Display in sidebar
alerts = check_for_alerts()
if alerts:
    st.sidebar.error(f"🚨 {len(alerts)} alerts")
    for alert in alerts:
        st.sidebar.warning(alert)
```

### 3.2 Collaboration Features

```python
def add_annotation_system():
    """Allow users to annotate recommendations"""
    rec_id = st.selectbox("Select recommendation", recs)

    annotation = st.text_area("Add note/comment")
    if st.button("Save Annotation"):
        save_annotation(rec_id, annotation, user_id=st.session_state.user)

def render_annotations(rec_id):
    """Show all annotations for a recommendation"""
    annotations = get_annotations(rec_id)
    for ann in annotations:
        st.info(f"📝 {ann['user']}: {ann['text']} ({ann['date']})")
```

### 3.3 Audit Trail

```python
def log_user_action(action, details):
    """Track all user interactions for audit"""
    audit_log = {
        'timestamp': datetime.now().isoformat(),
        'session_id': st.session_state.session_id,
        'action': action,  # 'search', 'export', 'filter', etc.
        'details': details,
    }
    append_to_audit_log(audit_log)
```

---

## Implementation Priority

### High Priority (Immediate Value)
1. **Faceted Search** - Users need better filtering
2. **Pagination** - Performance for large datasets
3. **Export Enhancements** - PDF and Excel formats
4. **spaCy NLP** - Better entity extraction

### Medium Priority (Significant Enhancement)
5. **Topic Modeling** - Automatic theme discovery
6. **Implementation Tracking** - Critical for measuring impact
7. **Dependency Mapping** - Reform sequencing
8. **Comparison Tools** - Side-by-side analysis

### Lower Priority (Nice to Have)
9. **Predictive Analytics** - Requires labeled training data
10. **Network Analysis** - Advanced visualization
11. **Mobile Responsiveness** - If mobile usage is significant
12. **Collaboration Features** - If multi-user

---

## Technical Debt Notes

1. **Hardcoded QUICK_WINS** (`dashboard.py:170-213`) - Should be derived from data
2. **Duplicate data loading functions** - Consolidate into single data layer
3. **No error boundaries** - Add try/catch for graceful degradation
4. **Missing type hints** - Add for better maintainability
5. **No tests** - Add pytest suite for critical functions

---

## Conclusion

The codebase is well-structured and production-ready. The recommended improvements would:

1. **Analytical:** Move from rule-based to ML-powered analysis, add implementation tracking, and improve scoring accuracy
2. **UI/UX:** Enhance search/filtering, improve performance, add export formats, and make the interface more accessible

The highest-impact improvements are:
- Faceted search with saved filters
- Topic modeling for automatic categorization
- Implementation status tracking
- PDF/Excel export capabilities

These changes would significantly increase the platform's value for policymakers and researchers.
