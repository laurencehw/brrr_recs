"""
Extract and analyze policy recommendations from BRRR reports
"""

import fitz  # PyMuPDF
import pandas as pd
from pathlib import Path
import re
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
BRRR_DIR = Path("brrr_reports")
OUTPUT_DIR = Path("analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

SECTORS = ["energy", "labour", "finance", "science_tech", "infrastructure", "trade"]

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file"""
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

def find_recommendation_sections(text):
    """Identify sections containing recommendations"""
    # Common patterns for recommendation sections
    patterns = [
        r'(?:^|\n)\s*(?:RECOMMENDATION|RECOMMENDATIONS)[\s:]*([^\n]*(?:\n(?!\n\s*[A-Z][A-Z\s]+:)[^\n]*)*)',
        r'(?:^|\n)\s*(?:The Committee recommends?)[^\n]*(?:\n(?!\n\s*[A-Z][A-Z\s]+:)[^\n]*)*',
        r'(?:^|\n)\s*(?:\d+\.?\s*RECOMMENDATION)[^\n]*(?:\n(?!\n\s*[A-Z][A-Z\s]+:)[^\n]*)*',
        r'(?:^|\n)\s*(?:Key recommendations?)[^\n]*(?:\n(?!\n\s*[A-Z][A-Z\s]+:)[^\n]*)*',
    ]

    sections = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            sections.append(match.group(0))

    return sections

def extract_recommendations_list(text):
    """Extract individual recommendations from text"""
    recommendations = []

    # Split by common delimiters
    lines = text.split('\n')
    current_rec = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            if current_rec:
                rec_text = ' '.join(current_rec)
                if len(rec_text) > 20:  # Minimum length filter
                    recommendations.append(rec_text)
                current_rec = []
            continue

        # Check if it's a new recommendation (numbered, bulleted, or "that...")
        if (re.match(r'^\d+\.?\d*\s', line) or
            re.match(r'^[•\-\*]\s', line) or
            line.lower().startswith('that ')):
            if current_rec:
                rec_text = ' '.join(current_rec)
                if len(rec_text) > 20:
                    recommendations.append(rec_text)
            current_rec = [line]
        else:
            if current_rec:
                current_rec.append(line)

    # Add last recommendation
    if current_rec:
        rec_text = ' '.join(current_rec)
        if len(rec_text) > 20:
            recommendations.append(rec_text)

    return recommendations

def categorize_recommendation(rec_text):
    """Categorize recommendation by theme"""
    rec_lower = rec_text.lower()

    categories = {
        'Budget/Fiscal': ['budget', 'fiscal', 'funding', 'appropriation', 'allocation', 'expenditure', 'revenue'],
        'Governance/Accountability': ['accountability', 'governance', 'oversight', 'compliance', 'audit', 'reporting', 'transparency'],
        'Capacity Building': ['capacity', 'skills', 'training', 'development', 'human resources', 'staffing'],
        'Infrastructure': ['infrastructure', 'construction', 'maintenance', 'facilities', 'equipment'],
        'Policy/Legislation': ['policy', 'legislation', 'law', 'regulation', 'act', 'bill', 'framework'],
        'Service Delivery': ['service delivery', 'implementation', 'roll-out', 'delivery', 'services'],
        'Institutional Reform': ['reform', 'restructure', 'transformation', 'institutional', 'reorganization'],
        'Monitoring & Evaluation': ['monitoring', 'evaluation', 'performance', 'indicators', 'targets', 'metrics'],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in rec_lower:
                return category

    return 'Other'

def analyze_report(pdf_path, sector, year):
    """Analyze a single BRRR report"""
    print(f"Analyzing: {pdf_path.name}")

    # Extract text
    text = extract_text_from_pdf(pdf_path)

    if not text:
        return []

    # Find recommendation sections
    rec_sections = find_recommendation_sections(text)

    # Extract individual recommendations
    all_recommendations = []
    for section in rec_sections:
        recs = extract_recommendations_list(section)
        all_recommendations.extend(recs)

    # If no structured recommendations found, try general extraction
    if not all_recommendations:
        # Look for "that" clauses which often indicate recommendations
        pattern = r'(?:recommends?\s+)?that\s+([^.]+\.)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            rec = match.group(0)
            if len(rec) > 30:
                all_recommendations.append(rec)

    # Structure the data
    results = []
    for rec in all_recommendations:
        # Clean up the recommendation text
        rec_clean = re.sub(r'\s+', ' ', rec).strip()

        results.append({
            'year': year,
            'sector': sector,
            'report': pdf_path.name,
            'recommendation': rec_clean,
            'category': categorize_recommendation(rec_clean),
            'length': len(rec_clean)
        })

    return results

def extract_key_themes(text):
    """Extract key themes and issues from report"""
    themes = {
        'Budget Execution': ['underspending', 'overspending', 'virement', 'rollover', 'under-expenditure'],
        'Unemployment': ['unemployment', 'job creation', 'employment', 'jobs'],
        'Energy Crisis': ['load shedding', 'loadshedding', 'energy crisis', 'electricity supply', 'eskom'],
        'Corruption': ['corruption', 'irregular expenditure', 'fruitless', 'wasteful'],
        'Service Delivery': ['service delivery', 'backlogs', 'access to services'],
        'Infrastructure': ['infrastructure', 'maintenance', 'construction'],
        'Skills Gap': ['skills', 'training', 'education'],
        'Regulatory': ['regulation', 'compliance', 'licensing'],
    }

    text_lower = text.lower()
    found_themes = []

    for theme, keywords in themes.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_themes.append(theme)
                break

    return list(set(found_themes))

def main():
    print("="*70)
    print("BRRR Reports Analysis - Extracting Policy Recommendations")
    print("="*70)

    all_recommendations = []
    report_summaries = []

    for sector in SECTORS:
        sector_dir = BRRR_DIR / sector

        if not sector_dir.exists():
            print(f"\nSkipping {sector} - no reports found")
            continue

        print(f"\n{'='*70}")
        print(f"Processing Sector: {sector.upper()}")
        print(f"{'='*70}")

        pdf_files = sorted(sector_dir.glob("*.pdf"))

        for pdf_file in pdf_files:
            # Extract year from filename
            year_match = re.search(r'(\d{4})', pdf_file.name)
            year = int(year_match.group(1)) if year_match else 0

            # Analyze report
            recommendations = analyze_report(pdf_file, sector, year)
            all_recommendations.extend(recommendations)

            # Extract full text for theme analysis
            full_text = extract_text_from_pdf(pdf_file)
            themes = extract_key_themes(full_text)

            report_summaries.append({
                'sector': sector,
                'year': year,
                'report': pdf_file.name,
                'recommendations_count': len(recommendations),
                'themes': ', '.join(themes),
                'file_size_kb': pdf_file.stat().st_size // 1024
            })

            print(f"  {pdf_file.name}: {len(recommendations)} recommendations")

    print(f"\n{'='*70}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total recommendations extracted: {len(all_recommendations)}")
    print(f"Total reports analyzed: {len(report_summaries)}")

    # Save to Excel
    if all_recommendations:
        df_recs = pd.DataFrame(all_recommendations)
        df_recs = df_recs.sort_values(['sector', 'year'])
        excel_path = OUTPUT_DIR / "recommendations_extracted.xlsx"

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_recs.to_excel(writer, sheet_name='All Recommendations', index=False)

            # Summary by sector
            sector_summary = df_recs.groupby('sector').agg({
                'recommendation': 'count',
                'category': lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A'
            }).rename(columns={'recommendation': 'count', 'category': 'top_category'})
            sector_summary.to_excel(writer, sheet_name='Summary by Sector')

            # Summary by year
            year_summary = df_recs.groupby('year')['recommendation'].count()
            year_summary.to_excel(writer, sheet_name='Summary by Year')

            # Summary by category
            category_summary = df_recs.groupby('category')['recommendation'].count().sort_values(ascending=False)
            category_summary.to_excel(writer, sheet_name='Summary by Category')

        print(f"\n✓ Recommendations saved to: {excel_path}")

    if report_summaries:
        df_summary = pd.DataFrame(report_summaries)
        df_summary = df_summary.sort_values(['sector', 'year'])
        summary_path = OUTPUT_DIR / "report_summaries.xlsx"
        df_summary.to_excel(summary_path, index=False)
        print(f"✓ Report summaries saved to: {summary_path}")

    # Save as JSON for further processing
    if all_recommendations:
        json_path = OUTPUT_DIR / "recommendations.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_recommendations, f, indent=2, ensure_ascii=False)
        print(f"✓ JSON data saved to: {json_path}")

    print(f"\n{'='*70}")
    print("Analysis complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
