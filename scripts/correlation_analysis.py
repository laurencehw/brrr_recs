"""
Correlation Analysis Module
===========================
Analyze relationships between recommendations and economic outcomes,
track patterns over time, and identify predictive indicators.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# Check for scipy
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# =============================================================================
# DATA LOADING
# =============================================================================

def load_recommendations() -> pd.DataFrame:
    """Load recommendations as DataFrame."""
    recs_path = Path(__file__).parent.parent / "analysis" / "recommendations.json"

    if not recs_path.exists():
        recs_path = Path(__file__).parent.parent / "analysis" / "recommendations_sample.json"

    if not recs_path.exists():
        return pd.DataFrame()

    with open(recs_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame(data.get('recommendations', []))


def load_economic_context() -> pd.DataFrame:
    """Load economic context data."""
    path = Path(__file__).parent.parent / "analysis" / "economic_context_with_loadshedding.csv"
    if path.exists():
        return pd.read_csv(path)

    path = Path(__file__).parent.parent / "analysis" / "economic_context_annual.csv"
    if path.exists():
        return pd.read_csv(path)

    return pd.DataFrame()


def load_loadshedding_data() -> Dict:
    """Load load-shedding data."""
    path = Path(__file__).parent.parent / "analysis" / "loadshedding_detailed.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# =============================================================================
# CORRELATION ANALYSIS
# =============================================================================

class CorrelationAnalyzer:
    """Analyze correlations between recommendations and outcomes."""

    def __init__(self):
        self.recs_df = load_recommendations()
        self.econ_df = load_economic_context()
        self.ls_data = load_loadshedding_data()

    def recommendation_counts_by_year(self, sector: Optional[str] = None) -> pd.Series:
        """Get recommendation counts by year, optionally filtered by sector."""
        df = self.recs_df.copy()
        if sector:
            df = df[df['sector'].str.contains(sector, case=False, na=False)]
        return df.groupby('year').size()

    def correlate_recommendations_with_indicators(self) -> Dict:
        """
        Correlate recommendation counts with economic indicators.
        Tests hypotheses like:
        - Do more recommendations correlate with worse outcomes?
        - Does sector-specific focus correlate with sector improvements?
        """
        if self.recs_df.empty or self.econ_df.empty:
            return {'error': 'Missing data'}

        results = {}

        # Get recommendation counts by year
        rec_counts = self.recommendation_counts_by_year()

        # Merge with economic data
        years = sorted(set(rec_counts.index) & set(self.econ_df['year']))

        if len(years) < 3:
            return {'error': 'Insufficient overlapping years for correlation'}

        # Prepare aligned data
        rec_values = [rec_counts.get(y, 0) for y in years]

        # Test correlations with each economic indicator
        indicators = ['unemployment_rate', 'gdp_growth_pct', 'days_with_loadshedding']

        for indicator in indicators:
            if indicator not in self.econ_df.columns:
                continue

            indicator_values = []
            for y in years:
                val = self.econ_df[self.econ_df['year'] == y][indicator].values
                if len(val) > 0:
                    indicator_values.append(val[0])
                else:
                    indicator_values.append(np.nan)

            # Remove NaN pairs
            valid_pairs = [(r, i) for r, i in zip(rec_values, indicator_values) if not np.isnan(i)]
            if len(valid_pairs) < 3:
                continue

            rec_clean = [p[0] for p in valid_pairs]
            ind_clean = [p[1] for p in valid_pairs]

            if SCIPY_AVAILABLE:
                corr, p_value = stats.pearsonr(rec_clean, ind_clean)
                results[indicator] = {
                    'correlation': round(corr, 3),
                    'p_value': round(p_value, 4),
                    'significant': p_value < 0.05,
                    'interpretation': self._interpret_correlation(corr, indicator),
                    'n_observations': len(valid_pairs)
                }
            else:
                # Simple correlation without scipy
                corr = np.corrcoef(rec_clean, ind_clean)[0, 1]
                results[indicator] = {
                    'correlation': round(corr, 3),
                    'p_value': None,
                    'significant': None,
                    'interpretation': self._interpret_correlation(corr, indicator),
                    'n_observations': len(valid_pairs)
                }

        return results

    def _interpret_correlation(self, corr: float, indicator: str) -> str:
        """Provide interpretation of correlation."""
        direction = "positive" if corr > 0 else "negative"
        strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"

        interpretations = {
            'unemployment_rate': f"A {direction} correlation suggests that more recommendations coincide with {'higher' if corr > 0 else 'lower'} unemployment.",
            'gdp_growth_pct': f"A {direction} correlation suggests that more recommendations coincide with {'higher' if corr > 0 else 'lower'} GDP growth.",
            'days_with_loadshedding': f"A {direction} correlation suggests that more recommendations coincide with {'more' if corr > 0 else 'fewer'} load-shedding days."
        }

        return f"{strength.capitalize()} {direction} correlation ({corr:.2f}). {interpretations.get(indicator, '')}"

    def sector_specific_correlations(self) -> Dict:
        """
        Analyze sector-specific correlations.
        E.g., Do energy recommendations correlate with load-shedding?
        """
        results = {}

        # Energy sector vs load-shedding
        if 'days_with_loadshedding' in self.econ_df.columns:
            energy_counts = self.recommendation_counts_by_year('energy')
            years = sorted(set(energy_counts.index) & set(self.econ_df['year']))

            if len(years) >= 3:
                energy_values = [energy_counts.get(y, 0) for y in years]
                ls_values = [
                    self.econ_df[self.econ_df['year'] == y]['days_with_loadshedding'].values[0]
                    for y in years
                    if len(self.econ_df[self.econ_df['year'] == y]['days_with_loadshedding'].values) > 0
                ]

                if len(ls_values) == len(energy_values) and SCIPY_AVAILABLE:
                    corr, p_value = stats.pearsonr(energy_values, ls_values)
                    results['energy_vs_loadshedding'] = {
                        'correlation': round(corr, 3),
                        'p_value': round(p_value, 4),
                        'interpretation': 'Positive correlation suggests Parliament responds to crises. Negative would suggest proactive recommendations preceding problems.',
                        'years_analyzed': years
                    }

        # Finance sector vs fiscal indicators (if available)
        finance_counts = self.recommendation_counts_by_year('finance')
        if not finance_counts.empty:
            results['finance_sector'] = {
                'total_recommendations': int(finance_counts.sum()),
                'avg_per_year': round(finance_counts.mean(), 1),
                'trend': 'increasing' if finance_counts.iloc[-1] > finance_counts.iloc[0] else 'stable/decreasing'
            }

        return results


# =============================================================================
# TIME SERIES ANALYSIS
# =============================================================================

class TimeSeriesAnalyzer:
    """Analyze trends and patterns over time."""

    def __init__(self):
        self.recs_df = load_recommendations()
        self.econ_df = load_economic_context()

    def recommendation_trends(self) -> Dict:
        """Analyze trends in recommendation patterns over time."""
        if self.recs_df.empty:
            return {}

        by_year = self.recs_df.groupby('year').agg({
            'recommendation': ['count', lambda x: x.str.len().mean()]
        }).round(2)

        by_year.columns = ['count', 'avg_length']
        by_year = by_year.reset_index()

        # Calculate trend (simple linear regression)
        years = by_year['year'].values
        counts = by_year['count'].values

        if len(years) >= 3 and SCIPY_AVAILABLE:
            slope, intercept, r_value, p_value, std_err = stats.linregress(years, counts)
            trend_direction = 'increasing' if slope > 0 else 'decreasing'
            trend_strength = 'strong' if abs(r_value) > 0.7 else 'moderate' if abs(r_value) > 0.4 else 'weak'
        else:
            slope = (counts[-1] - counts[0]) / (years[-1] - years[0]) if len(years) > 1 else 0
            trend_direction = 'increasing' if slope > 0 else 'decreasing'
            trend_strength = 'unknown'
            r_value = None
            p_value = None

        return {
            'yearly_data': by_year.to_dict('records'),
            'trend': {
                'direction': trend_direction,
                'strength': trend_strength,
                'slope': round(slope, 2) if slope else 0,
                'r_squared': round(r_value ** 2, 3) if r_value else None,
                'interpretation': f"Recommendations are {trend_direction} by ~{abs(slope):.1f} per year" if slope else "No clear trend"
            },
            'peak_year': int(by_year.loc[by_year['count'].idxmax(), 'year']),
            'min_year': int(by_year.loc[by_year['count'].idxmin(), 'year'])
        }

    def category_evolution(self) -> Dict:
        """Track how recommendation categories evolve over time."""
        if self.recs_df.empty or 'category' not in self.recs_df.columns:
            return {}

        # Get category counts by year
        cat_by_year = self.recs_df.groupby(['year', 'category']).size().unstack(fill_value=0)

        # Calculate which categories are growing/shrinking
        if len(cat_by_year) >= 2:
            first_year = cat_by_year.iloc[0]
            last_year = cat_by_year.iloc[-1]
            changes = ((last_year - first_year) / first_year.replace(0, 1) * 100).round(1)

            growing = changes[changes > 20].sort_values(ascending=False).head(5).to_dict()
            shrinking = changes[changes < -20].sort_values().head(5).to_dict()
        else:
            growing = {}
            shrinking = {}

        return {
            'category_by_year': cat_by_year.to_dict(),
            'growing_categories': growing,
            'shrinking_categories': shrinking
        }

    def economic_context_alignment(self) -> Dict:
        """Check if recommendation patterns align with economic cycles."""
        if self.recs_df.empty or self.econ_df.empty:
            return {}

        results = {}

        # Check if recommendations increase during economic downturns
        if 'gdp_growth_pct' in self.econ_df.columns:
            rec_counts = self.recs_df.groupby('year').size()

            # Find recession years (negative GDP growth)
            recession_years = self.econ_df[self.econ_df['gdp_growth_pct'] < 0]['year'].tolist()
            non_recession_years = self.econ_df[self.econ_df['gdp_growth_pct'] >= 0]['year'].tolist()

            recession_recs = [rec_counts.get(y, 0) for y in recession_years if y in rec_counts.index]
            non_recession_recs = [rec_counts.get(y, 0) for y in non_recession_years if y in rec_counts.index]

            if recession_recs and non_recession_recs:
                results['recession_response'] = {
                    'avg_recs_in_recession': round(np.mean(recession_recs), 1),
                    'avg_recs_in_growth': round(np.mean(non_recession_recs), 1),
                    'recession_years': recession_years,
                    'interpretation': 'Higher recommendations during recessions may indicate responsive oversight'
                }

        return results


# =============================================================================
# PREDICTIVE INDICATORS
# =============================================================================

class PredictiveAnalyzer:
    """Identify patterns that might predict outcomes."""

    def __init__(self):
        self.recs_df = load_recommendations()
        self.econ_df = load_economic_context()

    def identify_leading_indicators(self) -> Dict:
        """
        Test if certain recommendation patterns precede economic changes.
        Uses lagged correlation analysis.
        """
        if self.recs_df.empty or self.econ_df.empty:
            return {}

        results = {}

        # Get recommendation counts by year
        rec_counts = self.recs_df.groupby('year').size()

        # Test lagged correlations with economic indicators
        indicators = ['unemployment_rate', 'gdp_growth_pct', 'days_with_loadshedding']

        for indicator in indicators:
            if indicator not in self.econ_df.columns:
                continue

            indicator_series = self.econ_df.set_index('year')[indicator]

            lag_results = []
            for lag in range(1, 4):  # Test 1-3 year lags
                # Recommendations in year T vs indicator in year T+lag
                aligned_years = [y for y in rec_counts.index if y + lag in indicator_series.index]
                if len(aligned_years) < 3:
                    continue

                rec_values = [rec_counts[y] for y in aligned_years]
                ind_values = [indicator_series[y + lag] for y in aligned_years]

                if SCIPY_AVAILABLE:
                    corr, p_value = stats.pearsonr(rec_values, ind_values)
                    lag_results.append({
                        'lag_years': lag,
                        'correlation': round(corr, 3),
                        'p_value': round(p_value, 4),
                        'n_observations': len(aligned_years)
                    })

            if lag_results:
                # Find strongest lagged correlation
                best_lag = max(lag_results, key=lambda x: abs(x['correlation']))
                results[indicator] = {
                    'best_lag': best_lag['lag_years'],
                    'correlation_at_best_lag': best_lag['correlation'],
                    'all_lags': lag_results,
                    'interpretation': f"Strongest relationship found at {best_lag['lag_years']} year lag"
                }

        return results

    def recurring_theme_analysis(self) -> Dict:
        """
        Identify themes that appear repeatedly without resolution.
        Recurring themes indicate persistent problems.
        """
        if self.recs_df.empty:
            return {}

        # Keywords to track
        themes = {
            'irregular_expenditure': r'irregular\s+(expenditure|spending)',
            'vacancies': r'vacanc(y|ies)|unfilled\s+post',
            'procurement': r'procurement|tender',
            'consequence_management': r'consequence\s+management',
            'service_delivery': r'service\s+delivery',
            'load_shedding': r'load.?shedding|electricity\s+crisis',
            'corruption': r'corrupt|fraud|theft',
            'skills_shortage': r'skills?\s+(shortage|gap|development)'
        }

        theme_by_year = defaultdict(lambda: defaultdict(int))

        for _, row in self.recs_df.iterrows():
            text = str(row.get('recommendation', '')).lower()
            year = row.get('year')
            if not year:
                continue

            for theme, pattern in themes.items():
                import re
                if re.search(pattern, text, re.I):
                    theme_by_year[theme][year] += 1

        # Calculate persistence (how many years each theme appears)
        persistence = {}
        for theme, years in theme_by_year.items():
            persistence[theme] = {
                'years_appearing': len(years),
                'total_mentions': sum(years.values()),
                'by_year': dict(years),
                'is_persistent': len(years) >= 5,  # Appears in 5+ years
                'trend': 'increasing' if list(years.values())[-1] > list(years.values())[0] else 'stable/decreasing'
            }

        # Sort by persistence
        persistent_themes = sorted(
            [(k, v) for k, v in persistence.items() if v['is_persistent']],
            key=lambda x: x[1]['total_mentions'],
            reverse=True
        )

        return {
            'all_themes': persistence,
            'persistent_themes': [t[0] for t in persistent_themes],
            'most_mentioned': persistent_themes[0][0] if persistent_themes else None,
            'interpretation': 'Persistent themes indicate structural issues requiring fundamental reform rather than incremental fixes'
        }


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_correlation_analysis(save_results: bool = True) -> Dict:
    """Run comprehensive correlation analysis."""
    print("=" * 70)
    print("CORRELATION & TREND ANALYSIS")
    print("=" * 70)

    # Initialize analyzers
    corr_analyzer = CorrelationAnalyzer()
    ts_analyzer = TimeSeriesAnalyzer()
    pred_analyzer = PredictiveAnalyzer()

    results = {
        'analysis_date': pd.Timestamp.now().isoformat(),
        'scipy_available': SCIPY_AVAILABLE
    }

    # 1. Basic correlations
    print("\n" + "-" * 50)
    print("1. RECOMMENDATION-INDICATOR CORRELATIONS")
    print("-" * 50)

    correlations = corr_analyzer.correlate_recommendations_with_indicators()
    results['indicator_correlations'] = correlations

    for indicator, data in correlations.items():
        if isinstance(data, dict) and 'correlation' in data:
            print(f"  {indicator}: r={data['correlation']:.3f} {'*' if data.get('significant') else ''}")

    # 2. Sector-specific correlations
    print("\n" + "-" * 50)
    print("2. SECTOR-SPECIFIC ANALYSIS")
    print("-" * 50)

    sector_corr = corr_analyzer.sector_specific_correlations()
    results['sector_correlations'] = sector_corr

    if 'energy_vs_loadshedding' in sector_corr:
        print(f"  Energy recs vs load-shedding: r={sector_corr['energy_vs_loadshedding']['correlation']:.3f}")

    # 3. Time series trends
    print("\n" + "-" * 50)
    print("3. TIME SERIES TRENDS")
    print("-" * 50)

    trends = ts_analyzer.recommendation_trends()
    results['recommendation_trends'] = trends

    if trends.get('trend'):
        print(f"  Trend: {trends['trend']['direction']} ({trends['trend']['strength']})")
        print(f"  Peak year: {trends.get('peak_year')}")

    # 4. Category evolution
    cat_evolution = ts_analyzer.category_evolution()
    results['category_evolution'] = cat_evolution

    if cat_evolution.get('growing_categories'):
        print(f"  Growing categories: {list(cat_evolution['growing_categories'].keys())[:3]}")

    # 5. Economic cycle alignment
    econ_alignment = ts_analyzer.economic_context_alignment()
    results['economic_alignment'] = econ_alignment

    # 6. Predictive indicators
    print("\n" + "-" * 50)
    print("4. PREDICTIVE INDICATORS")
    print("-" * 50)

    leading_indicators = pred_analyzer.identify_leading_indicators()
    results['leading_indicators'] = leading_indicators

    for indicator, data in leading_indicators.items():
        if isinstance(data, dict):
            print(f"  {indicator}: best lag = {data.get('best_lag')} years")

    # 7. Recurring themes
    print("\n" + "-" * 50)
    print("5. RECURRING THEMES")
    print("-" * 50)

    recurring = pred_analyzer.recurring_theme_analysis()
    results['recurring_themes'] = recurring

    print(f"  Persistent themes: {recurring.get('persistent_themes', [])[:5]}")
    print(f"  Most mentioned: {recurring.get('most_mentioned')}")

    # Save results
    if save_results:
        output_dir = Path(__file__).parent.parent / "analysis"
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / "correlation_analysis.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            # Handle non-serializable types
            def convert(obj):
                if isinstance(obj, (np.integer, np.int64)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                return obj

            json.dump(results, f, indent=2, default=convert)
        print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    results = run_correlation_analysis()
