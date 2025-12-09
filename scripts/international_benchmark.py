"""
International Benchmarking
==========================
Compare South Africa's economic indicators with peer emerging markets
and BRICS+ nations to provide context for reform recommendations.
"""

import json
from pathlib import Path
import pandas as pd


# Peer country data (World Bank, IMF data 2023-2024)
PEER_COUNTRIES = {
    'South Africa': {
        'region': 'Sub-Saharan Africa',
        'income_group': 'Upper middle income',
        'gdp_per_capita_usd': 6_001,
        'gdp_growth_2023': 0.7,
        'gdp_growth_2024': 1.1,
        'unemployment_rate': 32.9,
        'youth_unemployment': 59.7,
        'inflation_2023': 5.9,
        'debt_to_gdp': 73.7,
        'gini_coefficient': 63.0,
        'ease_of_business_rank': 84,
        'corruption_perception_index': 41,
        'electricity_access_pct': 89.3,
        'renewable_energy_pct': 7.2,
        'population_millions': 60.4,
    },
    'Brazil': {
        'region': 'Latin America',
        'income_group': 'Upper middle income',
        'gdp_per_capita_usd': 10_412,
        'gdp_growth_2023': 2.9,
        'gdp_growth_2024': 2.2,
        'unemployment_rate': 7.8,
        'youth_unemployment': 17.0,
        'inflation_2023': 4.6,
        'debt_to_gdp': 87.0,
        'gini_coefficient': 52.9,
        'ease_of_business_rank': 124,
        'corruption_perception_index': 38,
        'electricity_access_pct': 100.0,
        'renewable_energy_pct': 48.4,
        'population_millions': 216.4,
    },
    'India': {
        'region': 'South Asia',
        'income_group': 'Lower middle income',
        'gdp_per_capita_usd': 2_612,
        'gdp_growth_2023': 7.2,
        'gdp_growth_2024': 6.8,
        'unemployment_rate': 7.7,
        'youth_unemployment': 23.2,
        'inflation_2023': 5.4,
        'debt_to_gdp': 83.1,
        'gini_coefficient': 35.7,
        'ease_of_business_rank': 63,
        'corruption_perception_index': 39,
        'electricity_access_pct': 99.6,
        'renewable_energy_pct': 19.1,
        'population_millions': 1428.6,
    },
    'Indonesia': {
        'region': 'East Asia & Pacific',
        'income_group': 'Upper middle income',
        'gdp_per_capita_usd': 4_788,
        'gdp_growth_2023': 5.0,
        'gdp_growth_2024': 5.1,
        'unemployment_rate': 5.3,
        'youth_unemployment': 14.0,
        'inflation_2023': 3.7,
        'debt_to_gdp': 39.3,
        'gini_coefficient': 38.2,
        'ease_of_business_rank': 73,
        'corruption_perception_index': 34,
        'electricity_access_pct': 97.3,
        'renewable_energy_pct': 12.3,
        'population_millions': 277.5,
    },
    'Mexico': {
        'region': 'Latin America',
        'income_group': 'Upper middle income',
        'gdp_per_capita_usd': 13_846,
        'gdp_growth_2023': 3.2,
        'gdp_growth_2024': 2.4,
        'unemployment_rate': 2.8,
        'youth_unemployment': 6.1,
        'inflation_2023': 5.5,
        'debt_to_gdp': 53.2,
        'gini_coefficient': 45.4,
        'ease_of_business_rank': 60,
        'corruption_perception_index': 31,
        'electricity_access_pct': 100.0,
        'renewable_energy_pct': 16.8,
        'population_millions': 128.9,
    },
    'Turkey': {
        'region': 'Europe & Central Asia',
        'income_group': 'Upper middle income',
        'gdp_per_capita_usd': 13_110,
        'gdp_growth_2023': 4.5,
        'gdp_growth_2024': 3.0,
        'unemployment_rate': 9.4,
        'youth_unemployment': 18.5,
        'inflation_2023': 53.9,
        'debt_to_gdp': 35.0,
        'gini_coefficient': 41.9,
        'ease_of_business_rank': 33,
        'corruption_perception_index': 36,
        'electricity_access_pct': 100.0,
        'renewable_energy_pct': 21.7,
        'population_millions': 85.3,
    },
    'Nigeria': {
        'region': 'Sub-Saharan Africa',
        'income_group': 'Lower middle income',
        'gdp_per_capita_usd': 1_621,
        'gdp_growth_2023': 2.9,
        'gdp_growth_2024': 3.3,
        'unemployment_rate': 33.3,
        'youth_unemployment': 42.5,
        'inflation_2023': 24.7,
        'debt_to_gdp': 38.8,
        'gini_coefficient': 35.1,
        'ease_of_business_rank': 131,
        'corruption_perception_index': 25,
        'electricity_access_pct': 59.5,
        'renewable_energy_pct': 19.4,
        'population_millions': 223.8,
    },
    'Egypt': {
        'region': 'Middle East & North Africa',
        'income_group': 'Lower middle income',
        'gdp_per_capita_usd': 3_614,
        'gdp_growth_2023': 3.8,
        'gdp_growth_2024': 4.0,
        'unemployment_rate': 7.1,
        'youth_unemployment': 21.5,
        'inflation_2023': 33.9,
        'debt_to_gdp': 95.8,
        'gini_coefficient': 31.5,
        'ease_of_business_rank': 114,
        'corruption_perception_index': 30,
        'electricity_access_pct': 100.0,
        'renewable_energy_pct': 11.5,
        'population_millions': 112.7,
    },
    'Kenya': {
        'region': 'Sub-Saharan Africa',
        'income_group': 'Lower middle income',
        'gdp_per_capita_usd': 2_099,
        'gdp_growth_2023': 5.6,
        'gdp_growth_2024': 5.0,
        'unemployment_rate': 5.7,
        'youth_unemployment': 13.7,
        'inflation_2023': 7.7,
        'debt_to_gdp': 70.2,
        'gini_coefficient': 38.7,
        'ease_of_business_rank': 56,
        'corruption_perception_index': 31,
        'electricity_access_pct': 76.5,
        'renewable_energy_pct': 90.5,
        'population_millions': 55.1,
    },
    'Vietnam': {
        'region': 'East Asia & Pacific',
        'income_group': 'Lower middle income',
        'gdp_per_capita_usd': 4_316,
        'gdp_growth_2023': 5.0,
        'gdp_growth_2024': 6.0,
        'unemployment_rate': 2.3,
        'youth_unemployment': 7.6,
        'inflation_2023': 3.3,
        'debt_to_gdp': 37.3,
        'gini_coefficient': 35.7,
        'ease_of_business_rank': 70,
        'corruption_perception_index': 42,
        'electricity_access_pct': 100.0,
        'renewable_energy_pct': 25.7,
        'population_millions': 100.4,
    },
}

# Key reform lessons from peer countries
REFORM_LESSONS = {
    'Vietnam': {
        'success_area': 'Economic Liberalization',
        'reforms': [
            'Doi Moi reforms: gradual market liberalization since 1986',
            'FDI-friendly policies attracting manufacturing',
            'Investment in education and skills development',
            'Infrastructure investment prioritization',
        ],
        'relevance_to_sa': 'Shows how gradual reforms can transform economy without shock therapy'
    },
    'Indonesia': {
        'success_area': 'Fiscal Discipline',
        'reforms': [
            'Post-1998 fiscal rules limiting debt',
            'Decentralization to improve service delivery',
            'Subsidy reforms (fuel price liberalization)',
            'Tax administration modernization',
        ],
        'relevance_to_sa': 'Demonstrates successful fiscal consolidation with social protection'
    },
    'India': {
        'success_area': 'Digital Transformation',
        'reforms': [
            'Aadhaar digital ID system reaching 1.3bn people',
            'UPI payment system revolutionizing fintech',
            'Direct benefit transfers reducing leakage',
            'GST unifying national tax system',
        ],
        'relevance_to_sa': 'Shows how technology can improve governance and reduce corruption'
    },
    'Kenya': {
        'success_area': 'Renewable Energy',
        'reforms': [
            '90%+ electricity from renewables (geothermal, wind, solar)',
            'Mobile money (M-Pesa) financial inclusion',
            'Tech hub development (Silicon Savannah)',
            'Regional trade integration (EAC)',
        ],
        'relevance_to_sa': 'Demonstrates renewable energy potential for Africa'
    },
    'Mexico': {
        'success_area': 'Trade Integration',
        'reforms': [
            'USMCA/NAFTA integration with North America',
            'Energy sector reforms (though partially reversed)',
            'Nearshoring opportunities from supply chain shifts',
            'Anti-corruption institutional reforms',
        ],
        'relevance_to_sa': 'Shows benefits and challenges of regional trade integration'
    },
    'Brazil': {
        'success_area': 'Social Programs',
        'reforms': [
            'Bolsa Família conditional cash transfers',
            'Unified Registry for social programs',
            'Independent central bank',
            'Agricultural productivity gains',
        ],
        'relevance_to_sa': 'Model for effective social protection with fiscal sustainability'
    },
}


def calculate_rankings():
    """Calculate where SA ranks among peers for each indicator."""
    df = pd.DataFrame(PEER_COUNTRIES).T
    
    rankings = {}
    
    # Higher is better
    for col in ['gdp_per_capita_usd', 'gdp_growth_2023', 'gdp_growth_2024', 
                'electricity_access_pct', 'renewable_energy_pct', 'corruption_perception_index']:
        if col in df.columns:
            rankings[col] = df[col].rank(ascending=False)
    
    # Lower is better
    for col in ['unemployment_rate', 'youth_unemployment', 'inflation_2023', 
                'debt_to_gdp', 'gini_coefficient', 'ease_of_business_rank']:
        if col in df.columns:
            rankings[col] = df[col].rank(ascending=True)
    
    return rankings


def generate_benchmark_analysis():
    """Generate comprehensive benchmarking analysis."""
    df = pd.DataFrame(PEER_COUNTRIES).T
    
    # Convert numeric columns explicitly
    numeric_cols = ['gdp_per_capita_usd', 'gdp_growth_2023', 'gdp_growth_2024', 
                    'unemployment_rate', 'youth_unemployment', 'inflation_2023',
                    'debt_to_gdp', 'gini_coefficient', 'ease_of_business_rank',
                    'corruption_perception_index', 'electricity_access_pct', 
                    'renewable_energy_pct', 'population_millions']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    sa = df.loc['South Africa']
    
    # Calculate averages (numeric columns only)
    peer_avg = df.drop('South Africa')[numeric_cols].mean()
    
    analysis = {
        'south_africa': sa.to_dict(),
        'peer_average': peer_avg.to_dict(),
        'comparison': {},
        'rankings': {},
        'strengths': [],
        'weaknesses': [],
        'reform_opportunities': [],
    }
    
    # Calculate rankings
    n_countries = len(df)
    
    for col in numeric_cols:
        if col not in df.columns:
            continue
        # Determine if higher or lower is better
        lower_is_better = col in ['unemployment_rate', 'youth_unemployment', 'inflation_2023',
                                   'debt_to_gdp', 'gini_coefficient', 'ease_of_business_rank']
        
        if lower_is_better:
            rank = int((df[col] <= sa[col]).sum())
        else:
            rank = int((df[col] >= sa[col]).sum())
        
        analysis['rankings'][col] = {
            'rank': rank,
            'out_of': n_countries,
            'sa_value': float(sa[col]),
            'peer_avg': float(peer_avg[col]),
            'gap': float(sa[col] - peer_avg[col]),
        }
    
    # Identify strengths and weaknesses
    for col, data in analysis['rankings'].items():
        if data['rank'] <= 3:
            analysis['strengths'].append({
                'indicator': col,
                'rank': data['rank'],
                'value': data['sa_value']
            })
        elif data['rank'] >= n_countries - 2:
            analysis['weaknesses'].append({
                'indicator': col,
                'rank': data['rank'],
                'value': data['sa_value']
            })
    
    # Reform opportunities based on peer lessons
    analysis['reform_lessons'] = REFORM_LESSONS
    
    return analysis


def generate_summary_stats():
    """Generate summary statistics for the benchmark."""
    df = pd.DataFrame(PEER_COUNTRIES).T
    
    stats = {
        'total_peers': len(df) - 1,
        'regions_covered': df['region'].nunique(),
        'sa_unemployment_vs_avg': float(df.loc['South Africa', 'unemployment_rate'] - df.drop('South Africa')['unemployment_rate'].mean()),
        'sa_gdp_growth_vs_avg': float(df.loc['South Africa', 'gdp_growth_2024'] - df.drop('South Africa')['gdp_growth_2024'].mean()),
        'sa_inequality_rank': int((df['gini_coefficient'] >= df.loc['South Africa', 'gini_coefficient']).sum()),
        'sa_debt_rank': int((df['debt_to_gdp'] >= df.loc['South Africa', 'debt_to_gdp']).sum()),
    }
    
    return stats


def main():
    print("=" * 60)
    print("International Benchmarking Analysis")
    print("=" * 60)
    
    # Generate analysis
    analysis = generate_benchmark_analysis()
    summary = generate_summary_stats()
    
    print(f"\nComparing South Africa with {summary['total_peers']} peer economies")
    print(f"Regions covered: {summary['regions_covered']}")
    
    print("\n" + "-" * 60)
    print("KEY INDICATORS - SA vs Peer Average")
    print("-" * 60)
    
    key_indicators = [
        ('gdp_growth_2024', 'GDP Growth 2024', '%', True),
        ('unemployment_rate', 'Unemployment', '%', False),
        ('youth_unemployment', 'Youth Unemployment', '%', False),
        ('debt_to_gdp', 'Debt-to-GDP', '%', False),
        ('gini_coefficient', 'Inequality (Gini)', '', False),
        ('renewable_energy_pct', 'Renewable Energy', '%', True),
    ]
    
    for col, name, unit, higher_better in key_indicators:
        data = analysis['rankings'].get(col, {})
        if data:
            direction = "↑" if (data['gap'] > 0) == higher_better else "↓"
            status = "✓" if (data['gap'] > 0) == higher_better else "✗"
            print(f"  {name}: SA {data['sa_value']}{unit} | Peers {data['peer_avg']:.1f}{unit} | Gap: {data['gap']:+.1f} {status}")
    
    print("\n" + "-" * 60)
    print("SA RANKINGS (out of 10 countries)")
    print("-" * 60)
    
    print("\n  STRENGTHS:")
    if analysis['strengths']:
        for s in analysis['strengths']:
            indicator = s['indicator'].replace('_', ' ').title()
            print(f"    #{s['rank']}: {indicator} ({s['value']})")
    else:
        print("    None identified in top 3")
    
    print("\n  WEAKNESSES:")
    if analysis['weaknesses']:
        for w in analysis['weaknesses']:
            indicator = w['indicator'].replace('_', ' ').title()
            print(f"    #{w['rank']}: {indicator} ({w['value']})")
    else:
        print("    None identified in bottom 3")
    
    print("\n" + "-" * 60)
    print("REFORM LESSONS FROM PEERS")
    print("-" * 60)
    
    for country, lesson in REFORM_LESSONS.items():
        print(f"\n  {country} - {lesson['success_area']}:")
        print(f"    Relevance: {lesson['relevance_to_sa']}")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    # Save full analysis
    output_path = output_dir / "international_benchmark.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"\nFull analysis saved to: {output_path}")
    
    # Save peer data for dashboard
    df = pd.DataFrame(PEER_COUNTRIES).T.reset_index()
    df.columns = ['country'] + list(df.columns[1:])
    df.to_csv(output_dir / "peer_country_data.csv", index=False)
    print(f"Peer data saved to: {output_dir / 'peer_country_data.csv'}")
    
    return analysis


if __name__ == "__main__":
    main()
