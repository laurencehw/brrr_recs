"""
Generate fiscally grounded policy memo with growth-constraint overlays.
Relies on the cleaned/scored workbook produced by prioritize_recommendations.py.
"""

import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ANALYSIS_DIR = Path("analysis")
OUTPUT_DIR = Path("analysis")
WORKBOOK = ANALYSIS_DIR / "recommendations_prioritized.xlsx"


def load_top_growth(limit=12):
    df = pd.read_excel(WORKBOOK, sheet_name="Top Growth Priorities")
    # Filter to fiscally disciplined, evidence-backed items
    df = df[df["fiscal_impact"].isin(["savings", "neutral", "low_cost"])]
    df = df[df["evidence_confidence"] != "low"]
    df = df.sort_values("growth_priority_score", ascending=False)
    return df.head(limit)


def render_bullet(row: dict, rank: int):
    rec = row.get("recommendation", "")
    if len(rec) > 320:
        rec = rec[:320].rsplit(" ", 1)[0] + "..."

    return f"""### {rank}. {row['sector'].upper()} ({row['year']})
**Growth Priority:** {row['growth_priority_score']:.1f} | Impact {row['impact_score']}/5 | Feas {row['feasibility_score']}/5 | Cost {row['cost_score']}/5  
**Constraint:** {row['binding_constraint']} | **Fiscal:** {row['fiscal_impact']} | **Owner:** {row.get('owner', 'line_dept')} | **Blocker:** {row.get('blocker_type', 'none')}

{rec}
"""


def generate_fiscal_memo():
    top = load_top_growth()

    memo = f"""
# SOUTH AFRICAN ECONOMIC REFORM AGENDA
## Fiscally-Grounded Policy Recommendations (Growth Lens)

**Integrating:** 10 years of BRRR recommendations (2015–2025)  
**With:** 2025 MTBPS fiscal guardrails  
**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Fiscal Context (MTBPS 2025)
- Debt stabilises around 77.9% of GDP; deficit narrows 4.7% → 2.7% by 2028/29; primary surplus rising.
- R19.3bn revenue overrun; no new tax hikes; fiscal headroom is thin.
- Commitments: R1tn infrastructure pipeline; R30.78bn private energy build (1,401 MW).
- Implication: Phase 1 must be neutral/savings; Phase 2 low-cost and self-funded; Phase 3 leans on private/PPP capital.

## Top 12 Growth-Priority, Fiscally Disciplined Actions
"""

    for idx, row in enumerate(top.itertuples(index=False), start=1):
        memo += render_bullet(row._asdict(), idx)
        memo += "\n"

    memo += """
## Phase Costs vs MTBPS (illustrative)
- Phase 1 (0–6m): admin/process fixes; savings from procurement deviations, customs leakage; target R5–10bn savings.
- Phase 2 (6–18m): low-cost enablers (visa IT lane, grid/wheeling process, metro loss-reduction pilots, water leak teams) funded via reprioritisation/conditional grants (R2–5bn).
- Phase 3 (18–36m): private/PPP-heavy (ports/rail slots, additional generation, broadband); minimal new public spend.

## Monitoring (headline KPIs)
- Load-shedding hours; MW connected; wheeling approvals.
- Port dwell/berth times; rail tonnage vs capacity.
- Visa approval days; backlog size.
- MIG/INEP/WSIG spend %; non-revenue water %; distribution loss %.
- Procurement deviations (count/value); irregular-expenditure trend.
- Food basket and transport cost indices; youth unemployment.
"""

    output_path = OUTPUT_DIR / "Executive_Summary_Fiscal.md"
    output_path.write_text(memo.strip() + "\n", encoding="utf-8")
    print(f"Memo written to {output_path}")


if __name__ == "__main__":
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"{WORKBOOK} not found. Run prioritize_recommendations.py first.")
    generate_fiscal_memo()
