"""
Prioritize recommendations with growth and fiscal overlays.
"""

import io
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Configuration
ANALYSIS_DIR = Path("analysis")
OUTPUT_DIR = Path("analysis")


def clean_text(text: str) -> str:
    """Basic cleaning to fix encoding noise and strip numeric debris."""
    if not isinstance(text, str):
        return ""
    cleaned = (
        text.encode("utf-8", "ignore")
        .decode("utf-8", "ignore")
        .replace("\u00a0", " ")
        .replace("\ufffd", " ")
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_numeric_noise(text: str) -> bool:
    """Drop rows that are mostly numbers or very short table fragments."""
    if len(text) < 40:
        return True
    digit_ratio = sum(ch.isdigit() for ch in text) / max(len(text), 1)
    return digit_ratio > 0.45


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove near-duplicate recommendations keeping the latest year.
    Uses a simple similarity check on normalized text.
    """
    df = df.copy()
    df["norm_text"] = df["recommendation"].str.lower().str.replace(r"[^a-z\s]", "", regex=True)
    df = df.sort_values(["year"], ascending=False)  # newest first

    seen = []
    keep_rows = []
    for idx, row in df.iterrows():
        txt = row["norm_text"]
        if any(SequenceMatcher(None, txt, s).ratio() > 0.85 for s in seen):
            continue
        seen.append(txt)
        keep_rows.append(idx)

    return df.loc[keep_rows].drop(columns=["norm_text"])


def calculate_feasibility_score(rec_text):
    """
    Score recommendation by feasibility/lift required (1-5, higher = easier)
    High feasibility (4-5): Administrative, policy clarification, reporting
    Medium feasibility (3): Process changes, modest funding, coordination
    Low feasibility (1-2): Major legislation, large budgets, complex reforms
    """
    rec_lower = rec_text.lower()

    # High feasibility indicators
    if any(word in rec_lower for word in [
        "report", "submit", "provide information", "inform", "clarify",
        "communicate", "explain", "respond", "update", "notify"
    ]):
        return 5

    # Medium-high feasibility
    if any(word in rec_lower for word in [
        "improve", "enhance", "strengthen", "coordinate", "collaborate",
        "streamline", "expedite", "accelerate", "prioritise", "prioritize"
    ]):
        return 4

    # Medium feasibility
    if any(word in rec_lower for word in [
        "develop", "implement", "establish", "create", "introduce",
        "review", "assess", "evaluate", "monitor"
    ]):
        return 3

    # Low feasibility
    if any(word in rec_lower for word in [
        "legislation", "act", "law", "constitutional", "parliament",
        "restructure", "major reform", "overhaul"
    ]):
        return 2

    # Very low feasibility
    if any(word in rec_lower for word in [
        "billion", "r billion", "significant funding", "major investment",
        "substantial resources"
    ]):
        return 1

    return 3  # Default medium


def calculate_impact_score(rec_text, category, sector):
    """
    Score potential impact (1-5, higher = greater impact)
    Consider: breadth of population affected, economic significance
    """
    rec_lower = rec_text.lower()

    impact = 3  # Default medium

    # High impact sectors
    if sector in ["energy", "finance", "labour"]:
        impact += 1

    # High impact keywords
    high_impact_keywords = [
        "unemployment", "job creation", "employment", "economic growth",
        "gdp", "investment", "energy crisis", "load shedding", "loadshedding",
        "poverty", "inequality", "service delivery", "corruption",
        "fiscal", "revenue", "tax", "budget deficit"
    ]

    if any(keyword in rec_lower for keyword in high_impact_keywords):
        impact += 1

    # Broad population impact
    if any(word in rec_lower for word in [
        "all", "national", "country-wide", "population", "citizens",
        "businesses", "economy", "sector-wide"
    ]):
        impact += 1

    # SMEs and broad economic base
    if any(word in rec_lower for word in ["sme", "small business", "informal sector"]):
        impact += 1

    return min(impact, 5)  # Cap at 5


def estimate_cost(rec_text):
    """
    Estimate implementation cost (1-5, lower = cheaper)
    1 = Very expensive (>R1bn)
    2 = Expensive (R100m-R1bn)
    3 = Moderate (R10m-R100m)
    4 = Low (R1m-R10m)
    5 = Minimal (<R1m, mostly administrative)
    """
    rec_lower = rec_text.lower()

    # Check for explicit funding mentions
    if re.search(r"r?\s*\d+\s*billion", rec_lower):
        return 1

    if re.search(r"r?\s*\d+\s*million", rec_lower):
        amount_match = re.search(r"r?\s*(\d+)\s*million", rec_lower)
        if amount_match:
            amount = int(amount_match.group(1))
            if amount > 100:
                return 2
            elif amount > 10:
                return 3
            else:
                return 4

    # Infer from activity type
    expensive_activities = [
        "construction", "infrastructure", "major investment", "capital",
        "build", "establish new", "procure", "large-scale"
    ]

    moderate_activities = [
        "system", "software", "technology", "equipment", "hiring",
        "training programme", "capacity building"
    ]

    cheap_activities = [
        "policy", "regulation", "report", "guideline", "framework",
        "clarification", "communication", "coordination", "monitoring"
    ]

    if any(word in rec_lower for word in expensive_activities):
        return 1

    if any(word in rec_lower for word in moderate_activities):
        return 3

    if any(word in rec_lower for word in cheap_activities):
        return 5

    return 3  # Default moderate


def calculate_roi_score(impact, cost, feasibility):
    """
    Calculate ROI score: (Impact * Feasibility) / Cost
    Normalized to 1-10 scale
    """
    roi = (impact * feasibility) / cost
    normalized_roi = ((roi - 0.2) / (25 - 0.2)) * 9 + 1  # 0.2=min, 25=max
    return round(normalized_roi, 2)


def classify_binding_constraint(rec_text: str) -> str:
    """Tag recommendation with the primary binding constraint."""
    rec_lower = rec_text.lower()
    mapping = {
        "energy": ["eskom", "load shedding", "loadshedding", "grid", "nersa", "ipp", "wheeling"],
        "logistics_ports_rail": ["transnet", "rail", "port", "terminal", "dwell", "berth", "container"],
        "water_sanitation": ["water use licence", "water-use licence", "waste water", "sanitation", "non-revenue water"],
        "permits_licenses": ["permit", "licence", "license", "authorisation", "authorization", "eia", "development charge"],
        "skills_visas": ["visa", "work permit", "critical skill", "home affairs"],
        "municipal_collapse": ["municipal", "equitable share", "section 71", "section 72", "mfico", "mig"],
        "crime_corruption": ["irregular expenditure", "fruitless", "wasteful", "siu", "npa", "forensic", "procurement deviation"],
        "competition_entry": ["competition commission", "market inquiry", "barrier to entry", "cartel", "price fixing"],
        "digital_connectivity": ["spectrum", "broadband", "4g", "5g", "fibre", "fiber"],
    }
    for label, keywords in mapping.items():
        if any(k in rec_lower for k in keywords):
            return label
    return "other"


def add_growth_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add growth/fiscal overlay fields and composite score."""
    df = df.copy()

    df["binding_constraint"] = df["recommendation"].apply(classify_binding_constraint)
    df["growth_elasticity"] = df["binding_constraint"].map({
        "energy": 5,
        "logistics_ports_rail": 5,
        "permits_licenses": 4,
        "skills_visas": 4,
        "municipal_collapse": 4,
        "water_sanitation": 4,
        "crime_corruption": 4,
        "competition_entry": 3,
        "digital_connectivity": 3,
    }).fillna(2)

    df["fiscal_impact"] = df.get("fiscal_impact", pd.Series(["neutral"] * len(df)))
    df["savings_window"] = df.get("savings_window", pd.Series(["6-18m"] * len(df)))
    df["funding_source"] = df.get("funding_source", pd.Series(["reprioritisation"] * len(df)))
    df["owner"] = df.get("owner", pd.Series(["line_dept"] * len(df)))
    df["blocker_type"] = df.get("blocker_type", pd.Series(["none"] * len(df)))
    df["evidence_confidence"] = df.get("evidence_confidence", pd.Series(["medium"] * len(df)))
    df["inequality_channel"] = df.get("inequality_channel", pd.Series(["none"] * len(df)))

    fiscal_weight = df["fiscal_impact"].map({
        "savings": 1.0,
        "neutral": 0.8,
        "low_cost": 0.5,
        "capex_heavy": 0.1,
    }).fillna(0.5)

    evidence_weight = df["evidence_confidence"].map({
        "high": 1.0,
        "medium": 0.7,
        "low": 0.4,
    }).fillna(0.5)

    blocker_penalty = df["blocker_type"].apply(
        lambda b: 0.2 if b in ["legislation", "institutional_capacity", "intergov_coord"] else 0
    )

    df["growth_priority_score"] = (
        0.35 * df["growth_elasticity"] +
        0.25 * df["roi_score"] +
        0.15 * df["feasibility_score"] +
        0.15 * fiscal_weight * 4 +
        0.10 * evidence_weight * 4 -
        blocker_penalty
    )

    return df


def identify_recurring_themes(recs_df):
    """Identify recommendations that appear multiple times across years."""
    theme_keywords = {
        "Budget Execution & Spending": ["underspend", "under-spend", "expenditure", "budget implementation", "spending"],
        "Irregular/Wasteful Expenditure": ["irregular expenditure", "fruitless", "wasteful", "consequence management"],
        "Vacant Posts & HR": ["vacant", "vacancies", "filled", "staffing", "human resources"],
        "Energy Crisis": ["load shedding", "loadshedding", "energy crisis", "electricity", "eskom"],
        "SOE Governance": ["state-owned", "soe", "public entities", "boards"],
        "Unemployment & Jobs": ["unemployment", "job creation", "employment", "jobs"],
        "SME Support": ["sme", "small business", "smme", "entrepreneurship"],
        "Compliance & Reporting": ["compliance", "reporting", "submit", "provide", "inform parliament"],
        "Procurement": ["procurement", "tender", "supply chain", "scm"],
        "Service Delivery": ["service delivery", "backlogs", "targets", "implementation"],
    }

    theme_counts = {}
    theme_years = {}

    for theme, keywords in theme_keywords.items():
        matches = recs_df[recs_df["recommendation"].str.lower().str.contains("|".join(keywords), na=False)]
        theme_counts[theme] = len(matches)
        theme_years[theme] = matches["year"].nunique()

    return theme_counts, theme_years


def identify_institutional_reforms(rec_text):
    """Identify if recommendation requires institutional reform."""
    rec_lower = rec_text.lower()

    reforms = []

    reform_patterns = {
        "Legislative Reform": ["amend act", "amend legislation", "new law", "bill", "legislative"],
        "Institutional Restructuring": ["restructure", "reorganize", "consolidate", "merge", "establish new entity"],
        "Governance Reform": ["board", "governance framework", "oversight", "accountability framework"],
        "Process Reform": ["streamline", "simplify", "process improvement", "efficiency"],
        "Capacity Building": ["training", "skills development", "capacity building", "competency"],
        "Systems & Technology": ["system", "database", "digital", "technology", "automation"],
        "Policy Framework": ["policy", "framework", "guidelines", "strategy", "regulations"],
    }

    for reform_type, keywords in reform_patterns.items():
        if any(keyword in rec_lower for keyword in keywords):
            reforms.append(reform_type)

    return ", ".join(reforms) if reforms else "None"


def main():
    print("=" * 80)
    print("BRRR Recommendations Prioritization Framework")
    print("=" * 80)

    json_path = ANALYSIS_DIR / "recommendations.json"
    with open(json_path, "r", encoding="utf-8") as f:
        recommendations = json.load(f)

    df = pd.DataFrame(recommendations)

    # Cleaning + dedup
    df["recommendation"] = df["recommendation"].apply(clean_text)
    df = df[~df["recommendation"].apply(is_numeric_noise)]
    df = deduplicate(df)

    print(f"\nTotal recommendations (cleaned & deduped): {len(df)}")
    print(f"Sectors: {df['sector'].nunique()}")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")

    # Apply scoring
    print("\nApplying scoring framework...")
    df["feasibility_score"] = df["recommendation"].apply(calculate_feasibility_score)
    df["impact_score"] = df.apply(
        lambda row: calculate_impact_score(row["recommendation"], row["category"], row["sector"]), axis=1
    )
    df["cost_score"] = df["recommendation"].apply(estimate_cost)
    df["roi_score"] = df.apply(
        lambda row: calculate_roi_score(row["impact_score"], row["cost_score"], row["feasibility_score"]), axis=1
    )

    # Institutional reforms
    df["institutional_reform"] = df["recommendation"].apply(identify_institutional_reforms)

    # Priority flags
    df["is_quick_win"] = (
        (df["feasibility_score"] >= 4) &
        (df["impact_score"] >= 4) &
        (df["cost_score"] >= 4)
    )

    df["is_high_priority"] = (
        (df["impact_score"] >= 4) &
        (df["feasibility_score"] >= 3) &
        (df["cost_score"] >= 3)
    )

    # Growth/fiscal overlays
    df = add_growth_scores(df)

    # Theme summaries
    print("\n" + "=" * 80)
    print("SCORING SUMMARY")
    print("=" * 80)
    print(f"\nQuick Wins (High impact, High feasibility, Low cost): {df['is_quick_win'].sum()}")
    print(f"High Priority (Strong scores across all dimensions): {df['is_high_priority'].sum()}")
    print(f"\nAverage Scores:")
    print(f"  Feasibility: {df['feasibility_score'].mean():.2f}/5")
    print(f"  Impact: {df['impact_score'].mean():.2f}/5")
    print(f"  Cost: {df['cost_score'].mean():.2f}/5 (higher = cheaper)")
    print(f"  ROI: {df['roi_score'].mean():.2f}/10")
    print(f"  Growth Priority: {df['growth_priority_score'].mean():.2f}")

    print("\n" + "=" * 80)
    print("RECURRING THEMES (mentioned across multiple reports/years)")
    print("=" * 80)
    theme_counts, theme_years = identify_recurring_themes(df)
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 10:
            years = theme_years[theme]
            print(f"  {theme:40s}: {count:4d} recommendations across {years} years")

    # Save prioritized recommendations
    df_sorted = df.sort_values("roi_score", ascending=False)
    df_growth_sorted = df.sort_values("growth_priority_score", ascending=False)

    output_path = OUTPUT_DIR / "recommendations_prioritized.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_sorted.to_excel(writer, sheet_name="All Prioritized", index=False)

        df[df["is_quick_win"]].sort_values("roi_score", ascending=False).to_excel(
            writer, sheet_name="Quick Wins", index=False
        )

        df[df["is_high_priority"]].sort_values("roi_score", ascending=False).to_excel(
            writer, sheet_name="High Priority", index=False
        )

        df_sorted.head(100).to_excel(writer, sheet_name="Top 100 ROI", index=False)
        df_growth_sorted.head(200).to_excel(writer, sheet_name="Top Growth Priorities", index=False)
        df.to_excel(writer, sheet_name="Cleaned", index=False)

        for sector in df["sector"].unique():
            df_sector = df[df["sector"] == sector].sort_values("roi_score", ascending=False)
            sheet_name = f"{sector.title()}"[:31]
            df_sector.to_excel(writer, sheet_name=sheet_name, index=False)

        df[df["year"] >= 2023].sort_values("roi_score", ascending=False).to_excel(
            writer, sheet_name="Recent (2023-2025)", index=False
        )

        df[df["institutional_reform"] != "None"].sort_values("roi_score", ascending=False).to_excel(
            writer, sheet_name="Institutional Reforms", index=False
        )

    print(f"\n-> Prioritized recommendations saved to: {output_path}")

    # Summary stats
    summary_stats = {
        "Total Recommendations": len(df),
        "Quick Wins": int(df["is_quick_win"].sum()),
        "High Priority": int(df["is_high_priority"].sum()),
        "Avg Feasibility": float(df["feasibility_score"].mean()),
        "Avg Impact": float(df["impact_score"].mean()),
        "Avg ROI": float(df["roi_score"].mean()),
        "Requiring Institutional Reform": int((df["institutional_reform"] != "None").sum()),
    }

    summary_path = OUTPUT_DIR / "prioritization_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2)

    print(f"-> Summary statistics saved to: {summary_path}")
    print("\n" + "=" * 80)
    print("Prioritization complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
