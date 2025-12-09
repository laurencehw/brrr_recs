"""
Add Load-Shedding Historical Data to BRRR Analysis

This script creates historical load-shedding data for South Africa
and correlates it with BRRR energy recommendations.

Data sourced from:
- Wikipedia: South African energy crisis
- Eskom announcements and reports
- News sources (BusinessTech, Daily Maverick, News24)

Load-shedding stages:
- Stage 1: <1000 MW removed, ~6% users affected
- Stage 2: <2000 MW removed, ~12.5% users affected
- Stage 3: <3000 MW removed, ~19% users affected
- Stage 4: <4000 MW removed, ~25% users affected
- Stage 5: <5000 MW removed, ~31% users affected
- Stage 6: <6000 MW removed, ~37% users affected (first time: Dec 2019)
- Stage 7: <7000 MW removed, ~44% users affected
- Stage 8: <8000 MW removed, ~50% users affected
"""

import pandas as pd
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"
OUTPUT_DIR = ANALYSIS_DIR

# Historical load-shedding data (annual summary)
# Sources: Wikipedia, Eskom, News reports
LOADSHEDDING_DATA = {
    2015: {
        "days_with_loadshedding": 90,  # Nov 2014 - Feb 2015 period spillover
        "max_stage": 3,
        "total_hours_estimated": 360,  # Rough estimate
        "period": "Second period (Nov 2014 - Feb 2015)",
        "key_events": [
            "Majuba coal silo collapse (Nov 2014)",
            "Stage 3 load shedding for first time (Dec 2014)",
            "Industry start-up after holidays caused resumption"
        ],
        "severity": "moderate"
    },
    2016: {
        "days_with_loadshedding": 15,
        "max_stage": 2,
        "total_hours_estimated": 30,
        "period": "Minimal - recovery period",
        "key_events": [
            "Relative stability as Medupi units came online",
            "Eskom credit rating downgraded to junk (S&P)"
        ],
        "severity": "low"
    },
    2017: {
        "days_with_loadshedding": 5,
        "max_stage": 2,
        "total_hours_estimated": 10,
        "period": "Minimal",
        "key_events": [
            "Kusile power station construction continues",
            "State capture investigations begin"
        ],
        "severity": "low"
    },
    2018: {
        "days_with_loadshedding": 10,
        "max_stage": 2,
        "total_hours_estimated": 20,
        "period": "Pre-crisis buildup",
        "key_events": [
            "NERSA denies Eskom 19.9% tariff increase",
            "Moody's downgrades Eskom to B2",
            "6000 unnecessary employees identified"
        ],
        "severity": "low"
    },
    2019: {
        "days_with_loadshedding": 52,
        "max_stage": 6,
        "total_hours_estimated": 530,
        "period": "Third and Fourth periods",
        "key_events": [
            "Feb-Mar: Third period (Stage 4)",
            "Dec 9: Stage 6 implemented FIRST TIME EVER",
            "Heavy rains flood coal stockpiles",
            "Sabotage allegations surface"
        ],
        "severity": "severe"
    },
    2020: {
        "days_with_loadshedding": 47,
        "max_stage": 4,
        "total_hours_estimated": 400,
        "period": "COVID-19 reduced demand, then resumption",
        "key_events": [
            "COVID lockdown reduced electricity demand",
            "March: Stage 4 due to Koeberg pump fault",
            "Load shedding largely suspended during lockdowns"
        ],
        "severity": "moderate"
    },
    2021: {
        "days_with_loadshedding": 120,
        "max_stage": 4,
        "total_hours_estimated": 1100,
        "period": "Fifth period begins (March 2021)",
        "key_events": [
            "March: Multiple power station breakdowns",
            "June: Stage 4 announced",
            "Oct: Stage 2 resumes after 77-day break",
            "Nov: Sabotage evidence at Lethabo found",
            "Eskom warns 4000-6000 MW additional capacity needed"
        ],
        "severity": "severe"
    },
    2022: {
        "days_with_loadshedding": 205,  # Record year
        "max_stage": 6,
        "total_hours_estimated": 2800,
        "period": "Record load shedding year",
        "key_events": [
            "June: NUMSA/NUM strikes cause Stage 6",
            "Sept: 50% generation capacity lost",
            "Dec: Army deployed to power stations",
            "Over 200 days of load shedding - worst ever"
        ],
        "severity": "critical"
    },
    2023: {
        "days_with_loadshedding": 310,  # Near continuous
        "max_stage": 6,
        "total_hours_estimated": 4500,
        "period": "Sustained crisis",
        "key_events": [
            "Feb: CEO André de Ruyter leaves amid crisis",
            "Mar: Electricity Minister Ramokgopa appointed",
            "April: Stage 6 due to plant failures",
            "Pylons collapsed in Pretoria (theft)",
            "Criminal syndicates identified within Eskom"
        ],
        "severity": "critical"
    },
    2024: {
        "days_with_loadshedding": 85,  # Jan-March before stability
        "max_stage": 6,
        "total_hours_estimated": 800,
        "period": "Crisis end - stability returns",
        "key_events": [
            "March 26: Load shedding ends after 3 years",
            "R254bn debt relief package for Eskom",
            "Generation capacity reaches 35,000 MW (6-year high)",
            "Full month without load shedding (April)",
            "Reduced demand from alternative energy uptake"
        ],
        "severity": "moderate"
    },
    2025: {
        "days_with_loadshedding": 5,  # Brief return in Feb
        "max_stage": 6,
        "total_hours_estimated": 50,
        "period": "Brief return",
        "key_events": [
            "Feb 22: Stage 6 returns unexpectedly",
            "Majuba and Camden failures",
            "NERSA rejects Eskom tariff increase request"
        ],
        "severity": "low"
    }
}


def create_loadshedding_dataframe():
    """Create a pandas DataFrame from load-shedding data"""
    records = []
    for year, data in LOADSHEDDING_DATA.items():
        records.append({
            "year": year,
            "days_with_loadshedding": data["days_with_loadshedding"],
            "max_stage": data["max_stage"],
            "total_hours_estimated": data["total_hours_estimated"],
            "severity": data["severity"],
            "period_description": data["period"]
        })
    return pd.DataFrame(records)


def calculate_severity_score(row):
    """Calculate a severity score (0-100) based on days and stage"""
    # Weight: days (60%) + max_stage (40%)
    day_score = min(row['days_with_loadshedding'] / 365 * 100, 100) * 0.6
    stage_score = (row['max_stage'] / 8) * 100 * 0.4
    return round(day_score + stage_score, 1)


def create_economic_impact_estimate(row):
    """Estimate economic impact based on research figures
    
    Sources:
    - Stage 6 costs R4bn per day (Alexforbes estimate)
    - Stage 4 costs ~R2.5bn per day
    - Average cost per hour at Stage 4: ~R250m
    """
    # Conservative estimate: R200m per hour average
    hourly_cost_rm = 200  # R million per hour
    return row['total_hours_estimated'] * hourly_cost_rm


def save_loadshedding_data():
    """Save load-shedding data to files"""
    print("Creating load-shedding historical dataset...")
    
    df = create_loadshedding_dataframe()
    df['severity_score'] = df.apply(calculate_severity_score, axis=1)
    df['estimated_cost_rmillion'] = df.apply(create_economic_impact_estimate, axis=1)
    
    # Save CSV
    csv_path = OUTPUT_DIR / "loadshedding_annual.csv"
    df.to_csv(csv_path, index=False)
    print(f"✓ Saved {csv_path}")
    
    # Save detailed JSON with events
    json_data = {
        "summary": {
            "period_covered": "2015-2025",
            "total_days_loadshedding": int(df['days_with_loadshedding'].sum()),
            "total_hours_estimated": int(df['total_hours_estimated'].sum()),
            "total_estimated_cost_rbillion": round(df['estimated_cost_rmillion'].sum() / 1000, 1),
            "worst_year": int(df.loc[df['days_with_loadshedding'].idxmax(), 'year']),
            "first_stage_6": 2019,
            "crisis_peak": "2022-2023"
        },
        "annual_data": LOADSHEDDING_DATA,
        "stage_definitions": {
            "stage_1": {"mw_removed": 1000, "percent_affected": 6, "hours_per_4_days": 6},
            "stage_2": {"mw_removed": 2000, "percent_affected": 12.5, "hours_per_4_days": 12},
            "stage_3": {"mw_removed": 3000, "percent_affected": 19, "hours_per_4_days": 18},
            "stage_4": {"mw_removed": 4000, "percent_affected": 25, "hours_per_4_days": 24},
            "stage_5": {"mw_removed": 5000, "percent_affected": 31, "hours_per_4_days": 30},
            "stage_6": {"mw_removed": 6000, "percent_affected": 37, "hours_per_4_days": 36},
            "stage_7": {"mw_removed": 7000, "percent_affected": 44, "hours_per_4_days": 42},
            "stage_8": {"mw_removed": 8000, "percent_affected": 50, "hours_per_4_days": 48}
        },
        "sources": [
            "Wikipedia: South African energy crisis",
            "Eskom load shedding announcements",
            "BusinessTech, Daily Maverick, News24 reports",
            "Alexforbes economic cost estimates",
            "CSIR power generation statistics"
        ]
    }
    
    json_path = OUTPUT_DIR / "loadshedding_detailed.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"✓ Saved {json_path}")
    
    return df, json_data


def correlate_with_electricity_data():
    """Load electricity availability and correlate with load-shedding"""
    try:
        econ_path = OUTPUT_DIR / "economic_context_annual.csv"
        if econ_path.exists():
            econ_df = pd.read_csv(econ_path)
            ls_df = create_loadshedding_dataframe()
            ls_df['severity_score'] = ls_df.apply(calculate_severity_score, axis=1)
            
            # Merge
            merged = econ_df.merge(ls_df[['year', 'days_with_loadshedding', 'max_stage', 
                                          'severity_score', 'total_hours_estimated']], 
                                   on='year', how='left')
            
            # Save merged
            merged_path = OUTPUT_DIR / "economic_context_with_loadshedding.csv"
            merged.to_csv(merged_path, index=False)
            print(f"✓ Saved merged dataset: {merged_path}")
            
            return merged
    except Exception as e:
        print(f"Warning: Could not merge with economic data: {e}")
    return None


def print_summary(df, json_data):
    """Print a summary of load-shedding data"""
    print("\n" + "="*70)
    print("SOUTH AFRICAN LOAD-SHEDDING HISTORY (2015-2025)")
    print("="*70)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total days with load-shedding: {json_data['summary']['total_days_loadshedding']}")
    print(f"   Total hours estimated: {json_data['summary']['total_hours_estimated']:,}")
    print(f"   Estimated economic cost: R{json_data['summary']['total_estimated_cost_rbillion']} billion")
    print(f"   Worst year: {json_data['summary']['worst_year']}")
    print(f"   First Stage 6: December {json_data['summary']['first_stage_6']}")
    
    print(f"\n📅 ANNUAL BREAKDOWN:")
    print(f"{'Year':<6} {'Days':<8} {'Max Stage':<12} {'Hours':<10} {'Severity':<12} {'Est Cost (Rbn)':<15}")
    print("-"*70)
    
    for _, row in df.iterrows():
        severity_emoji = {"low": "🟢", "moderate": "🟡", "severe": "🟠", "critical": "🔴"}
        emoji = severity_emoji.get(LOADSHEDDING_DATA[row['year']]['severity'], "⚪")
        cost_bn = row['total_hours_estimated'] * 200 / 1000
        print(f"{int(row['year']):<6} {int(row['days_with_loadshedding']):<8} {int(row['max_stage']):<12} "
              f"{int(row['total_hours_estimated']):<10} {emoji} {LOADSHEDDING_DATA[row['year']]['severity']:<10} "
              f"R{cost_bn:.1f}bn")
    
    print("\n⚡ KEY MILESTONES:")
    print("   • Dec 2019: Stage 6 implemented for FIRST TIME")
    print("   • 2022: Record 205+ days of load-shedding")
    print("   • 2023: Sustained crisis, near-continuous outages")
    print("   • Mar 2024: Stability returns after R254bn bailout")


def main():
    print("="*60)
    print("ADDING LOAD-SHEDDING DATA TO BRRR ANALYSIS")
    print("="*60)
    
    # Create and save data
    df, json_data = save_loadshedding_data()
    
    # Correlate with existing economic context
    merged = correlate_with_electricity_data()
    
    # Print summary
    print_summary(df, json_data)
    
    print("\n" + "="*60)
    print("LOAD-SHEDDING DATA INTEGRATION COMPLETE")
    print("="*60)
    print(f"\nOutput files:")
    print(f"  - analysis/loadshedding_annual.csv")
    print(f"  - analysis/loadshedding_detailed.json")
    if merged is not None:
        print(f"  - analysis/economic_context_with_loadshedding.csv")


if __name__ == "__main__":
    main()
