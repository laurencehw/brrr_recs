"""
Integrate fiscal context from MTBPS into BRRR recommendations
Add fiscal feasibility scoring based on 2025 budget constraints
"""

import pandas as pd
import json
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ANALYSIS_DIR = Path("analysis")

def calculate_fiscal_feasibility(row):
    """
    Calculate fiscal feasibility score (1-4) based on MTBPS constraints
    4 = Fiscally neutral/positive (highest feasibility)
    3 = Low incremental cost (<R100m/year)
    2 = Moderate cost (R100m-R1bn/year)
    1 = High cost (>R1bn/year)
    """
    rec_lower = row['recommendation'].lower()
    cost_score = row['cost_score']
    category = row['category'].lower() if isinstance(row['category'], str) else ''

    # Category 4: Fiscally neutral or positive
    if any(keyword in rec_lower for keyword in [
        'reduce irregular', 'reduce wasteful', 'reduce fruitless',
        'improve collection', 'improve compliance', 'consequence management',
        'report', 'monitor', 'oversight', 'accountability',
        'streamline', 'simplify', 'coordinate'
    ]):
        return 4

    # Administrative improvements are fiscally neutral
    if cost_score == 5:  # Minimal cost
        return 4

    # Category 3: Low incremental cost
    if cost_score == 4:  # Low cost (R1m-R10m)
        return 3

    # Category 2: Moderate cost
    if cost_score == 3:  # Moderate (R10m-R100m)
        # Check if it's revenue-generating or efficiency-creating
        if any(keyword in rec_lower for keyword in [
            'efficiency', 'optimization', 'automation', 'digitization'
        ]):
            return 3  # Upgrade to low-moderate
        return 2

    # Category 1: High cost
    if cost_score <= 2:  # Expensive or very expensive
        return 1

    return 2  # Default moderate

def categorize_mtbps_alignment(row):
    """Categorize how well recommendation aligns with MTBPS priorities"""
    rec_lower = row['recommendation'].lower()
    sector = row['sector']

    # High alignment areas from MTBPS
    high_alignment_keywords = {
        'Infrastructure': ['infrastructure', 'maintenance', 'project management', 'delivery capacity'],
        'Energy': ['energy', 'electricity', 'generation', 'transmission', 'grid', 'private sector'],
        'Tax Admin': ['tax', 'revenue', 'collection', 'sars', 'compliance'],
        'SOE Reform': ['state-owned', 'soe', 'eskom', 'transnet', 'governance', 'operational efficiency'],
        'Public Sector Efficiency': ['expenditure management', 'budget execution', 'irregular expenditure',
                                      'procurement', 'digitalization', 'automation'],
        'Employment': ['job creation', 'employment', 'unemployment', 'skills', 'training']
    }

    alignments = []

    for priority_area, keywords in high_alignment_keywords.items():
        if any(keyword in rec_lower for keyword in keywords):
            alignments.append(priority_area)

    if not alignments:
        return 'General Reform'

    return ', '.join(alignments[:2])  # Top 2 alignments

def calculate_fiscal_priority_score(row):
    """
    Calculate overall fiscal priority score combining:
    - Original ROI score
    - Fiscal feasibility
    - MTBPS alignment
    """
    roi = row['roi_score']
    fiscal_feasibility = row['fiscal_feasibility']
    has_alignment = row['mtbps_alignment'] != 'General Reform'

    # Weight factors
    fiscal_weight = 3.0  # Fiscal feasibility is critical given constraints
    alignment_bonus = 1.5 if has_alignment else 0

    # Normalized fiscal priority (1-10 scale)
    fiscal_priority = (
        (roi * 0.4) +  # 40% original ROI
        (fiscal_feasibility * 2.0) +  # 40% fiscal feasibility (scaled to 8)
        alignment_bonus  # 15% alignment bonus
    )

    return round(fiscal_priority, 2)

def main():
    print("="*80)
    print("Integrating Fiscal Context from 2025 MTBPS into Recommendations")
    print("="*80)

    # Load prioritized recommendations
    df = pd.read_excel(ANALYSIS_DIR / "recommendations_prioritized.xlsx",
                      sheet_name="All Prioritized")

    print(f"\nTotal recommendations: {len(df)}")

    # Add fiscal feasibility scores
    print("\nCalculating fiscal feasibility scores...")
    df['fiscal_feasibility'] = df.apply(calculate_fiscal_feasibility, axis=1)

    # Add MTBPS alignment categorization
    print("Categorizing MTBPS alignment...")
    df['mtbps_alignment'] = df.apply(categorize_mtbps_alignment, axis=1)

    # Calculate fiscal priority score
    print("Calculating fiscal priority scores...")
    df['fiscal_priority_score'] = df.apply(calculate_fiscal_priority_score, axis=1)

    # Identify top priorities under fiscal constraints
    df['fiscally_optimal'] = (
        (df['fiscal_feasibility'] >= 3) &  # Low cost or fiscally neutral
        (df['impact_score'] >= 4) &  # High impact
        (df['feasibility_score'] >= 3)  # Reasonable feasibility
    )

    # Priority tiers based on fiscal reality
    def assign_fiscal_tier(row):
        if row['fiscal_feasibility'] == 4 and row['impact_score'] >= 4:
            return 'Tier 1: Immediate (Fiscally Neutral, High Impact)'
        elif row['fiscal_feasibility'] >= 3 and row['impact_score'] >= 4:
            return 'Tier 2: Near-Term (Low Cost, High Impact)'
        elif row['fiscal_feasibility'] >= 3 and row['impact_score'] >= 3:
            return 'Tier 3: Medium-Term (Low Cost, Moderate Impact)'
        elif row['fiscal_feasibility'] == 2:
            return 'Tier 4: Phased (Moderate Cost - requires business case)'
        else:
            return 'Tier 5: Future (High Cost - awaiting fiscal space)'

    df['fiscal_tier'] = df.apply(assign_fiscal_tier, axis=1)

    # Summary statistics
    print("\n" + "="*80)
    print("FISCAL FEASIBILITY SUMMARY")
    print("="*80)

    feasibility_dist = df['fiscal_feasibility'].value_counts().sort_index(ascending=False)
    print("\nFiscal Feasibility Distribution:")
    labels = {
        4: "Fiscally Neutral/Positive",
        3: "Low Incremental Cost (<R100m)",
        2: "Moderate Cost (R100m-R1bn)",
        1: "High Cost (>R1bn)"
    }

    for level, count in feasibility_dist.items():
        pct = (count / len(df)) * 100
        print(f"  {labels.get(level, 'Unknown'):35s}: {count:4d} ({pct:5.1f}%)")

    print("\n" + "="*80)
    print("MTBPS ALIGNMENT SUMMARY")
    print("="*80)

    alignment_dist = df['mtbps_alignment'].value_counts()
    print(f"\nTop 10 MTBPS Alignment Areas:")
    for area, count in alignment_dist.head(10).items():
        print(f"  {area:45s}: {count:4d}")

    print("\n" + "="*80)
    print("FISCAL TIER DISTRIBUTION")
    print("="*80)

    tier_dist = df['fiscal_tier'].value_counts()
    print()
    for tier, count in sorted(tier_dist.items()):
        pct = (count / len(df)) * 100
        print(f"  {tier:60s}: {count:4d} ({pct:5.1f}%)")

    print(f"\n" + "="*80)
    print(f"FISCALLY OPTIMAL RECOMMENDATIONS: {df['fiscally_optimal'].sum()}")
    print("="*80)
    print("(High impact + High feasibility + Low fiscal cost)")

    # Resort by fiscal priority
    df_sorted = df.sort_values('fiscal_priority_score', ascending=False)

    # Save enhanced dataset
    output_path = ANALYSIS_DIR / "recommendations_with_fiscal_context.xlsx"

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # All recommendations by fiscal priority
        df_sorted.to_excel(writer, sheet_name='All by Fiscal Priority', index=False)

        # Fiscally optimal recommendations
        df_optimal = df[df['fiscally_optimal']].sort_values('fiscal_priority_score', ascending=False)
        df_optimal.to_excel(writer, sheet_name='Fiscally Optimal', index=False)

        # By fiscal tier
        for tier in sorted(df['fiscal_tier'].unique()):
            df_tier = df[df['fiscal_tier'] == tier].sort_values('fiscal_priority_score', ascending=False)
            sheet_name = f"Tier {tier[5]}"  # Extract tier number
            df_tier.to_excel(writer, sheet_name=sheet_name, index=False)

        # By MTBPS alignment
        priority_alignments = [
            'Infrastructure', 'Energy', 'Public Sector Efficiency',
            'SOE Reform', 'Employment', 'Tax Admin'
        ]

        for alignment in priority_alignments:
            df_aligned = df[df['mtbps_alignment'].str.contains(alignment, case=False, na=False)]
            if len(df_aligned) > 0:
                df_aligned = df_aligned.sort_values('fiscal_priority_score', ascending=False)
                sheet_name = alignment[:31]  # Excel limit
                df_aligned.to_excel(writer, sheet_name=sheet_name, index=False)

        # Top 100 fiscal priorities
        df_sorted.head(100).to_excel(writer, sheet_name='Top 100 Fiscal Priority', index=False)

        # Recent + fiscally feasible (2023-2025)
        df_recent_feasible = df[
            (df['year'] >= 2023) &
            (df['fiscal_feasibility'] >= 3)
        ].sort_values('fiscal_priority_score', ascending=False)
        df_recent_feasible.to_excel(writer, sheet_name='Recent & Feasible', index=False)

    print(f"\n✓ Enhanced recommendations saved to: {output_path}")

    # Save summary statistics
    summary_stats = {
        'total_recommendations': len(df),
        'fiscally_optimal': int(df['fiscally_optimal'].sum()),
        'tier_1_immediate': int((df['fiscal_tier'].str.contains('Tier 1')).sum()),
        'tier_2_near_term': int((df['fiscal_tier'].str.contains('Tier 2')).sum()),
        'high_mtbps_alignment': int((df['mtbps_alignment'] != 'General Reform').sum()),
        'fiscal_feasibility_distribution': feasibility_dist.to_dict(),
        'avg_fiscal_priority_score': float(df['fiscal_priority_score'].mean())
    }

    summary_path = ANALYSIS_DIR / "fiscal_integration_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary_stats, f, indent=2)

    print(f"✓ Summary statistics saved to: {summary_path}")

    print("\n" + "="*80)
    print("Integration Complete!")
    print("="*80)

if __name__ == "__main__":
    main()
