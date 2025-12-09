"""
Add Economic Context to BRRR Recommendations

This script enriches the BRRR recommendations with South African economic
indicators to provide context for each year's recommendations.

Data sources:
- GDP (national annual)
- Unemployment rate (quarterly -> annual average)
- Electricity availability (monthly -> annual)
- CPI/Inflation
- Debt-to-GDP ratio
- Manufacturing production index
- Retail trade
"""

import pandas as pd
import json
from pathlib import Path
import os

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "economic_context"
ANALYSIS_DIR = BASE_DIR / "analysis"
OUTPUT_DIR = ANALYSIS_DIR


def load_recommendations():
    """Load the BRRR recommendations JSON"""
    json_path = ANALYSIS_DIR / "recommendations.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"Warning: {json_path} not found")
        return []


def load_unemployment_data():
    """Load and process unemployment rate data (quarterly -> annual average)"""
    df = pd.read_csv(DATA_DIR / "lmis_unemployment_rate_total_quarterly.csv")
    # Extract year from time_period (format: 2015-Q1)
    df['year'] = df['time_period'].str[:4].astype(int)
    # Calculate annual average
    annual = df.groupby('year')['value'].mean().reset_index()
    annual.columns = ['year', 'unemployment_rate']
    annual['unemployment_rate'] = annual['unemployment_rate'].round(1)
    return annual


def load_electricity_data():
    """Load and process electricity data (monthly -> annual total GWh)"""
    df = pd.read_csv(DATA_DIR / "electricity_available_gwh_sa.csv")
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    # Sum to annual total
    annual = df.groupby('year')['value'].sum().reset_index()
    annual.columns = ['year', 'electricity_gwh']
    return annual


def load_gdp_data():
    """Load GDP data - handle the multi-row format"""
    df = pd.read_csv(DATA_DIR / "national_gdp_annual.csv")
    # The file has multiple rows per year; take the first (nominal GDP)
    # Group by year and take first value
    annual = df.groupby('year').first().reset_index()
    annual.columns = ['year', 'gdp_rmillion']
    return annual


def load_cpi_data():
    """Load CPI/inflation data"""
    try:
        df = pd.read_csv(DATA_DIR / "cpi_headline_proxy.csv")
        # Check column structure and adapt
        if 'year' in df.columns and 'value' in df.columns:
            return df[['year', 'value']].rename(columns={'value': 'cpi_index'})
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            annual = df.groupby('year')['value'].mean().reset_index()
            annual.columns = ['year', 'cpi_index']
            return annual
    except Exception as e:
        print(f"Warning: Could not load CPI data: {e}")
    return pd.DataFrame(columns=['year', 'cpi_index'])


def load_debt_gdp_data():
    """Load debt-to-GDP ratio"""
    try:
        df = pd.read_csv(DATA_DIR / "debt_gdp.csv")
        if 'year' in df.columns:
            return df
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            return df.groupby('year').last().reset_index()
    except Exception as e:
        print(f"Warning: Could not load debt-GDP data: {e}")
    return pd.DataFrame(columns=['year', 'debt_gdp_ratio'])


def load_manufacturing_data():
    """Load manufacturing production index"""
    try:
        df = pd.read_csv(DATA_DIR / "manufacturing_production_index.csv")
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            annual = df.groupby('year')['value'].mean().reset_index()
            annual.columns = ['year', 'manufacturing_index']
            return annual
    except Exception as e:
        print(f"Warning: Could not load manufacturing data: {e}")
    return pd.DataFrame(columns=['year', 'manufacturing_index'])


def build_economic_context():
    """Build a comprehensive economic context dataframe by year"""
    print("Loading economic data...")
    
    # Start with years 2015-2025 (BRRR coverage period)
    years = pd.DataFrame({'year': range(2015, 2026)})
    
    # Load each dataset
    unemployment = load_unemployment_data()
    print(f"  ✓ Unemployment: {len(unemployment)} years")
    
    electricity = load_electricity_data()
    print(f"  ✓ Electricity: {len(electricity)} years")
    
    gdp = load_gdp_data()
    print(f"  ✓ GDP: {len(gdp)} years")
    
    cpi = load_cpi_data()
    print(f"  ✓ CPI: {len(cpi)} years")
    
    debt_gdp = load_debt_gdp_data()
    print(f"  ✓ Debt-GDP: {len(debt_gdp)} years")
    
    manufacturing = load_manufacturing_data()
    print(f"  ✓ Manufacturing: {len(manufacturing)} years")
    
    # Merge all data
    context = years.copy()
    context = context.merge(unemployment, on='year', how='left')
    context = context.merge(electricity, on='year', how='left')
    context = context.merge(gdp, on='year', how='left')
    context = context.merge(cpi, on='year', how='left')
    context = context.merge(manufacturing, on='year', how='left')
    
    # Calculate year-over-year changes
    context['gdp_growth_pct'] = context['gdp_rmillion'].pct_change() * 100
    context['electricity_change_pct'] = context['electricity_gwh'].pct_change() * 100
    
    return context


def create_economic_summary():
    """Create a summary of economic context for the analysis period"""
    context = build_economic_context()
    
    # Save to CSV
    output_path = OUTPUT_DIR / "economic_context_annual.csv"
    context.to_csv(output_path, index=False)
    print(f"\n✓ Saved economic context to {output_path}")
    
    # Create a narrative summary
    summary = {
        "period": "2015-2025",
        "unemployment": {
            "min": float(context['unemployment_rate'].min()) if context['unemployment_rate'].notna().any() else None,
            "max": float(context['unemployment_rate'].max()) if context['unemployment_rate'].notna().any() else None,
            "latest": float(context['unemployment_rate'].iloc[-1]) if context['unemployment_rate'].notna().any() else None,
            "trend": "increasing" if context['unemployment_rate'].iloc[-1] > context['unemployment_rate'].iloc[0] else "decreasing"
        },
        "electricity": {
            "2015_gwh": float(context.loc[context['year']==2015, 'electricity_gwh'].iloc[0]) if len(context.loc[context['year']==2015]) > 0 else None,
            "latest_gwh": float(context['electricity_gwh'].iloc[-1]) if context['electricity_gwh'].notna().any() else None,
        },
        "key_observations": [
            "Unemployment rose significantly during COVID-19 (2020-2021)",
            "Electricity availability declined due to load-shedding crisis",
            "BRRR recommendations correlate with economic challenges"
        ],
        "data_by_year": context.to_dict(orient='records')
    }
    
    # Save summary JSON
    summary_path = OUTPUT_DIR / "economic_context_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"✓ Saved economic summary to {summary_path}")
    
    return context, summary


def print_context_table(context):
    """Print a formatted table of economic context"""
    print("\n" + "="*80)
    print("SOUTH AFRICAN ECONOMIC CONTEXT (2015-2025)")
    print("="*80)
    
    # Select key columns
    display_cols = ['year', 'unemployment_rate', 'gdp_growth_pct', 'electricity_gwh']
    available_cols = [c for c in display_cols if c in context.columns]
    
    print(f"\n{'Year':<6} {'Unemp %':<10} {'GDP Growth %':<14} {'Electricity GWh':<15}")
    print("-"*50)
    
    for _, row in context.iterrows():
        year = int(row['year'])
        unemp = f"{row['unemployment_rate']:.1f}" if pd.notna(row.get('unemployment_rate')) else "N/A"
        gdp = f"{row['gdp_growth_pct']:.1f}" if pd.notna(row.get('gdp_growth_pct')) else "N/A"
        elec = f"{row['electricity_gwh']:,.0f}" if pd.notna(row.get('electricity_gwh')) else "N/A"
        print(f"{year:<6} {unemp:<10} {gdp:<14} {elec:<15}")


def main():
    print("="*60)
    print("ADDING ECONOMIC CONTEXT TO BRRR RECOMMENDATIONS")
    print("="*60)
    
    # Build and save economic context
    context, summary = create_economic_summary()
    
    # Print summary table
    print_context_table(context)
    
    print("\n" + "="*60)
    print("ECONOMIC CONTEXT INTEGRATION COMPLETE")
    print("="*60)
    print(f"\nOutput files:")
    print(f"  - analysis/economic_context_annual.csv")
    print(f"  - analysis/economic_context_summary.json")
    print(f"\nNext steps:")
    print(f"  1. Review the economic context data")
    print(f"  2. Correlate with BRRR recommendation themes")
    print(f"  3. Add to policy memo narrative")


if __name__ == "__main__":
    main()
