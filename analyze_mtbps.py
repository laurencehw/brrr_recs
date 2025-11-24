"""
Extract and analyze fiscal context from 2025 MTBPS documents
"""

import fitz  # PyMuPDF
import re
import json
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MTBPS_DIR = Path("mtbps_2025")
OUTPUT_DIR = Path("analysis")

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting from {pdf_path.name}: {str(e)}")
        return ""

def extract_fiscal_metrics(text):
    """Extract key fiscal metrics from MTBPS text"""
    metrics = {}

    # GDP growth
    gdp_match = re.search(r'(?:GDP growth|economic growth).*?(\d+\.?\d*)(?:\s*per cent|\s*%)', text, re.IGNORECASE)
    if gdp_match:
        metrics['gdp_growth_pct'] = float(gdp_match.group(1))

    # Budget deficit/surplus
    deficit_patterns = [
        r'(?:budget|fiscal)\s+deficit.*?(\d+\.?\d*)\s*per cent of GDP',
        r'deficit.*?(\d+\.?\d*)\s*%\s*of GDP',
        r'main budget deficit.*?R(\d+\.?\d*)\s*billion'
    ]
    for pattern in deficit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metrics['budget_deficit'] = match.group(1)
            break

    # Debt levels
    debt_patterns = [
        r'(?:gross|national)\s+debt.*?(\d+\.?\d*)\s*per cent of GDP',
        r'debt-to-GDP.*?(\d+\.?\d*)\s*per cent'
    ]
    for pattern in debt_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metrics['debt_to_gdp_pct'] = float(match.group(1))
            break

    # Revenue
    revenue_match = re.search(r'(?:total|gross)\s+(?:revenue|tax revenue).*?R(\d+\.?\d*)\s*billion', text, re.IGNORECASE)
    if revenue_match:
        metrics['revenue_bn'] = float(revenue_match.group(1))

    # Expenditure
    expenditure_match = re.search(r'(?:total|consolidated)\s+(?:expenditure|spending).*?R(\d+\.?\d*)\s*(?:billion|trillion)', text, re.IGNORECASE)
    if expenditure_match:
        metrics['expenditure_bn'] = float(expenditure_match.group(1))

    return metrics

def extract_sector_allocations(text):
    """Extract budget allocations for priority sectors"""

    # Define sector keywords and variations
    sectors = {
        'Energy': ['electricity', 'energy', 'mineral resources and energy', 'eskom'],
        'Labour': ['employment and labour', 'department of labour', 'employment'],
        'Finance': ['national treasury', 'finance', 'revenue'],
        'Science & Technology': ['science and innovation', 'higher education', 'research'],
        'Infrastructure': ['public works', 'infrastructure', 'construction'],
        'Trade & Industry': ['trade and industry', 'dtic', 'industrial development']
    }

    allocations = {}

    # Look for budget allocation patterns
    # Pattern: Department/Sector name followed by allocation amount
    for sector_name, keywords in sectors.items():
        for keyword in keywords:
            # Search for patterns like "Department of X receives R1.5 billion" or "X: R1.5bn"
            patterns = [
                rf'{keyword}.*?R(\d+\.?\d*)\s*(?:billion|bn)',
                rf'{keyword}.*?R(\d+\.?\d*)\s*(?:million|m)',
                rf'R(\d+\.?\d*)\s*(?:billion|bn).*?{keyword}',
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount = float(match.group(1))
                    unit = 'billion' if 'billion' in match.group(0).lower() or 'bn' in match.group(0).lower() else 'million'

                    if unit == 'million':
                        amount = amount / 1000  # Convert to billions

                    if sector_name not in allocations or amount > allocations[sector_name].get('amount_bn', 0):
                        allocations[sector_name] = {
                            'amount_bn': round(amount, 2),
                            'keyword': keyword
                        }

    return allocations

def extract_fiscal_challenges(text):
    """Extract mentioned fiscal challenges and constraints"""
    challenges = []

    challenge_keywords = [
        'fiscal constraint', 'budget pressure', 'fiscal consolidation',
        'debt burden', 'revenue shortfall', 'expenditure ceiling',
        'fiscal sustainability', 'debt stabilization', 'fiscal risk',
        'budget deficit', 'fiscal stress', 'limited fiscal space'
    ]

    # Find sentences containing challenge keywords
    sentences = re.split(r'[.!?]\s+', text)

    for sentence in sentences:
        sentence_lower = sentence.lower()
        for keyword in challenge_keywords:
            if keyword in sentence_lower and len(sentence) > 50:
                # Clean up and add
                clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                if len(clean_sentence) > 100:
                    challenges.append({
                        'theme': keyword,
                        'context': clean_sentence[:500]
                    })
                    break  # One theme per sentence

    # Deduplicate similar challenges
    unique_challenges = []
    seen_themes = set()

    for challenge in challenges[:20]:  # Limit to top 20
        if challenge['theme'] not in seen_themes:
            unique_challenges.append(challenge)
            seen_themes.add(challenge['theme'])

    return unique_challenges

def extract_reform_priorities(text):
    """Extract mentioned reform priorities from MTBPS"""
    reforms = []

    # Look for sections about reforms
    reform_sections = [
        r'(?:reform|reforms|structural reform).*?(?:\n.*?){0,10}',
        r'(?:priority|priorities).*?(?:\n.*?){0,10}',
        r'(?:intervention|interventions).*?(?:\n.*?){0,10}'
    ]

    reform_keywords = [
        'energy reform', 'soe reform', 'state-owned enterprise',
        'public service', 'efficiency', 'procurement reform',
        'economic reform', 'structural reform', 'fiscal reform',
        'governance', 'accountability', 'institutional reform'
    ]

    sentences = re.split(r'[.!?]\s+', text)

    for sentence in sentences:
        sentence_lower = sentence.lower()
        for keyword in reform_keywords:
            if keyword in sentence_lower and len(sentence) > 50:
                clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                if len(clean_sentence) > 80:
                    reforms.append({
                        'area': keyword,
                        'detail': clean_sentence[:400]
                    })
                    break

    # Deduplicate
    unique_reforms = []
    seen_areas = set()

    for reform in reforms[:15]:
        if reform['area'] not in seen_areas:
            unique_reforms.append(reform)
            seen_areas.add(reform['area'])

    return unique_reforms

def analyze_mtbps():
    """Main analysis function"""

    print("="*80)
    print("Analyzing 2025 MTBPS - Extracting Fiscal Context")
    print("="*80)

    # Extract from main MTBPS
    mtbps_path = MTBPS_DIR / "Full_MTBPS.pdf"

    if not mtbps_path.exists():
        print(f"Error: {mtbps_path} not found")
        return

    print(f"\nExtracting text from {mtbps_path.name}...")
    mtbps_text = extract_text_from_pdf(mtbps_path)
    print(f"  Extracted {len(mtbps_text):,} characters")

    # Extract fiscal metrics
    print("\nExtracting fiscal metrics...")
    fiscal_metrics = extract_fiscal_metrics(mtbps_text)

    print("\n  Key Fiscal Metrics:")
    for key, value in fiscal_metrics.items():
        print(f"    {key}: {value}")

    # Extract sector allocations
    print("\nExtracting sector budget allocations...")
    allocations = extract_sector_allocations(mtbps_text)

    if allocations:
        print("\n  Priority Sector Allocations:")
        for sector, data in allocations.items():
            print(f"    {sector}: R{data['amount_bn']:.1f}bn")
    else:
        print("  (No specific allocations found in summary - check AENE for details)")

    # Also check AENE
    aene_path = MTBPS_DIR / "Full_AENE.pdf"
    if aene_path.exists():
        print(f"\nExtracting text from {aene_path.name}...")
        aene_text = extract_text_from_pdf(aene_path)
        print(f"  Extracted {len(aene_text):,} characters")

        print("\nExtracting detailed allocations from AENE...")
        aene_allocations = extract_sector_allocations(aene_text)

        if aene_allocations:
            print("\n  AENE Sector Allocations:")
            for sector, data in aene_allocations.items():
                print(f"    {sector}: R{data['amount_bn']:.1f}bn")

            # Merge allocations
            for sector, data in aene_allocations.items():
                if sector not in allocations or data['amount_bn'] > allocations.get(sector, {}).get('amount_bn', 0):
                    allocations[sector] = data

    # Extract fiscal challenges
    print("\nExtracting fiscal challenges...")
    challenges = extract_fiscal_challenges(mtbps_text)
    print(f"  Found {len(challenges)} key fiscal challenges")

    # Extract reform priorities
    print("\nExtracting reform priorities mentioned...")
    reforms = extract_reform_priorities(mtbps_text)
    print(f"  Found {len(reforms)} reform priorities")

    # Compile results
    mtbps_analysis = {
        'fiscal_metrics': fiscal_metrics,
        'sector_allocations': allocations,
        'fiscal_challenges': challenges,
        'reform_priorities': reforms,
        'document_date': '2025 MTBPS',
        'extraction_note': 'Automated extraction - verify key figures against source documents'
    }

    # Save results
    output_path = OUTPUT_DIR / "mtbps_fiscal_context.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mtbps_analysis, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Analysis saved to: {output_path}")

    # Create summary report
    summary = f"""
# 2025 MTBPS FISCAL CONTEXT SUMMARY

## Key Fiscal Metrics

"""
    for key, value in fiscal_metrics.items():
        summary += f"- **{key.replace('_', ' ').title()}**: {value}\n"

    summary += f"""

## Priority Sector Budget Allocations

"""
    if allocations:
        for sector, data in sorted(allocations.items(), key=lambda x: x[1]['amount_bn'], reverse=True):
            summary += f"- **{sector}**: R{data['amount_bn']:.1f} billion\n"
    else:
        summary += "*Detailed sector allocations require manual extraction from AENE*\n"

    summary += f"""

## Key Fiscal Challenges Identified

"""
    for i, challenge in enumerate(challenges[:10], 1):
        summary += f"{i}. **{challenge['theme'].title()}**\n"
        summary += f"   - {challenge['context'][:200]}...\n\n"

    summary += f"""

## Government Reform Priorities (from MTBPS)

"""
    for i, reform in enumerate(reforms, 1):
        summary += f"{i}. **{reform['area'].title()}**\n"
        summary += f"   - {reform['detail'][:250]}...\n\n"

    summary_path = OUTPUT_DIR / "mtbps_fiscal_summary.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"✓ Summary report saved to: {summary_path}")

    print("\n" + "="*80)
    print("MTBPS Analysis Complete")
    print("="*80)
    print(f"\nNext step: Cross-reference BRRR recommendations with fiscal constraints")

    return mtbps_analysis

if __name__ == "__main__":
    analyze_mtbps()
