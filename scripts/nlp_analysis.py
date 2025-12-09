"""
NLP Analysis for BRRR Recommendations
=====================================
Performs sentiment analysis, entity extraction, and topic modeling
on budget recommendations to identify patterns and priorities.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd


def load_recommendations():
    """Load the BRRR recommendations data."""
    recs_path = Path(__file__).parent.parent / "analysis" / "recommendations.json"
    
    if not recs_path.exists():
        print(f"Error: {recs_path} not found")
        return []
    
    with open(recs_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, list):
            return data
        return data.get('recommendations', [])


# Key economic/policy terms to extract
POLICY_ENTITIES = {
    'fiscal': ['budget', 'expenditure', 'revenue', 'deficit', 'surplus', 'fiscal', 'appropriation', 
               'allocation', 'spending', 'treasury', 'taxation', 'tariff'],
    'governance': ['accountability', 'transparency', 'oversight', 'compliance', 'audit', 'governance',
                   'corruption', 'irregular', 'fruitless', 'wasteful', 'consequence', 'disciplinary'],
    'service_delivery': ['service delivery', 'infrastructure', 'maintenance', 'backlog', 'capacity',
                         'performance', 'targets', 'outcomes', 'outputs', 'implementation'],
    'human_resources': ['vacancy', 'staff', 'personnel', 'appointment', 'recruitment', 'skills',
                        'training', 'capacity building', 'human capital', 'employment'],
    'financial_management': ['cash flow', 'accrual', 'asset', 'liability', 'debt', 'procurement',
                             'supply chain', 'contract', 'tender', 'financial statements'],
    'soe': ['soe', 'state-owned', 'eskom', 'transnet', 'prasa', 'denel', 'saa', 'sanral', 'entity'],
    'social': ['poverty', 'inequality', 'unemployment', 'social grant', 'welfare', 'housing',
               'education', 'health', 'water', 'sanitation', 'electricity'],
    'economic': ['gdp', 'growth', 'investment', 'economic', 'industrialisation', 'trade', 'export',
                 'import', 'competitiveness', 'productivity', 'inflation']
}

# Sentiment indicators
POSITIVE_INDICATORS = [
    'improve', 'increase', 'enhance', 'strengthen', 'progress', 'achieve', 'success',
    'effective', 'efficient', 'positive', 'growth', 'opportunity', 'recommend', 'support',
    'develop', 'advance', 'better', 'good', 'excellent', 'commend', 'encourage'
]

NEGATIVE_INDICATORS = [
    'concern', 'decline', 'decrease', 'fail', 'failure', 'inadequate', 'insufficient',
    'poor', 'weak', 'underperform', 'delay', 'overdue', 'irregular', 'wasteful', 'fruitless',
    'corrupt', 'mismanagement', 'crisis', 'problem', 'issue', 'challenge', 'risk',
    'threat', 'deteriorate', 'collapse', 'lack', 'shortage', 'deficit', 'breach'
]

URGENCY_INDICATORS = [
    'urgent', 'immediate', 'critical', 'priority', 'must', 'imperative', 'essential',
    'crucial', 'vital', 'serious', 'severe', 'grave', 'alarming', 'emergency',
    'expedite', 'accelerate', 'without delay', 'as soon as possible', 'forthwith'
]


def extract_entities(text):
    """Extract policy-relevant entities from text."""
    text_lower = text.lower()
    found_entities = defaultdict(list)
    
    for category, terms in POLICY_ENTITIES.items():
        for term in terms:
            if term in text_lower:
                found_entities[category].append(term)
    
    return dict(found_entities)


def analyze_sentiment(text):
    """Analyze sentiment of recommendation text."""
    text_lower = text.lower()
    
    positive_count = sum(1 for word in POSITIVE_INDICATORS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_INDICATORS if word in text_lower)
    urgency_count = sum(1 for word in URGENCY_INDICATORS if word in text_lower)
    
    # Calculate sentiment score (-1 to 1)
    total = positive_count + negative_count
    if total == 0:
        sentiment_score = 0
    else:
        sentiment_score = (positive_count - negative_count) / total
    
    # Determine sentiment label
    if sentiment_score > 0.2:
        sentiment = 'positive'
    elif sentiment_score < -0.2:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    # Urgency level
    if urgency_count >= 3:
        urgency = 'high'
    elif urgency_count >= 1:
        urgency = 'medium'
    else:
        urgency = 'low'
    
    return {
        'sentiment': sentiment,
        'sentiment_score': round(sentiment_score, 3),
        'urgency': urgency,
        'urgency_count': urgency_count,
        'positive_indicators': positive_count,
        'negative_indicators': negative_count
    }


def extract_monetary_values(text):
    """Extract monetary values mentioned in text."""
    # Pattern for South African Rand values
    patterns = [
        r'R\s?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|thousand|bn|m|k)?',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(billion|million|thousand|bn|m|k)?\s*rand',
    ]
    
    values = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            value, unit = match
            value = float(value.replace(',', ''))
            
            # Convert to base rand
            unit = unit.lower() if unit else ''
            if unit in ['billion', 'bn']:
                value *= 1_000_000_000
            elif unit in ['million', 'm']:
                value *= 1_000_000
            elif unit in ['thousand', 'k']:
                value *= 1_000
            
            values.append(value)
    
    return values


def extract_timeframes(text):
    """Extract timeframes and deadlines mentioned."""
    patterns = [
        r'(\d{4}/\d{2,4})',  # Financial years like 2023/24
        r'(20\d{2})',  # Years
        r'(\d+)\s*(day|week|month|year)s?',  # Duration
        r'(immediate|urgent|within|by|before|after|during)',  # Time indicators
    ]
    
    timeframes = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        timeframes.extend(matches)
    
    return timeframes


def analyze_recommendation(rec):
    """Perform full NLP analysis on a single recommendation."""
    text = rec.get('recommendation', '') or rec.get('text', '')
    
    if not text:
        return None
    
    analysis = {
        'id': rec.get('id'),
        'department': rec.get('sector'),  # Field is 'sector' in the data
        'year': rec.get('year'),
        'committee': rec.get('report'),
        'category': rec.get('category'),
        'text_length': len(text),
        'word_count': len(text.split()),
    }
    
    # Sentiment analysis
    sentiment = analyze_sentiment(text)
    analysis.update(sentiment)
    
    # Entity extraction
    entities = extract_entities(text)
    analysis['entities'] = entities
    analysis['entity_categories'] = list(entities.keys())
    analysis['entity_count'] = sum(len(v) for v in entities.values())
    
    # Monetary values
    monetary = extract_monetary_values(text)
    analysis['monetary_values'] = monetary
    analysis['has_monetary_reference'] = len(monetary) > 0
    analysis['total_monetary_value'] = sum(monetary) if monetary else 0
    
    return analysis


def generate_nlp_summary(analyses):
    """Generate summary statistics from NLP analyses."""
    df = pd.DataFrame(analyses)
    
    summary = {
        'total_recommendations': len(df),
        'sentiment_distribution': df['sentiment'].value_counts().to_dict(),
        'urgency_distribution': df['urgency'].value_counts().to_dict(),
        'average_sentiment_score': round(df['sentiment_score'].mean(), 3),
        'average_word_count': round(df['word_count'].mean(), 1),
        'recommendations_with_monetary_refs': int(df['has_monetary_reference'].sum()),
        'total_monetary_referenced': df['total_monetary_value'].sum(),
    }
    
    # Entity category frequency
    all_categories = []
    for cats in df['entity_categories']:
        all_categories.extend(cats)
    summary['entity_category_frequency'] = dict(Counter(all_categories))
    
    # By department
    dept_sentiment = df.groupby('department').agg({
        'sentiment_score': 'mean',
        'urgency_count': 'mean',
        'entity_count': 'mean'
    }).round(3).to_dict('index')
    summary['by_department'] = dept_sentiment
    
    # By year
    year_sentiment = df.groupby('year').agg({
        'sentiment_score': 'mean',
        'urgency_count': 'mean',
        'entity_count': 'sum'
    }).round(3).to_dict('index')
    summary['by_year'] = year_sentiment
    
    # Top concerns (high urgency + negative sentiment)
    high_concern = df[(df['urgency'] == 'high') & (df['sentiment'] == 'negative')]
    summary['high_concern_count'] = len(high_concern)
    summary['high_concern_departments'] = high_concern['department'].value_counts().head(10).to_dict()
    
    return summary


def main():
    print("=" * 60)
    print("NLP Analysis of BRRR Recommendations")
    print("=" * 60)
    
    # Load data
    recommendations = load_recommendations()
    if not recommendations:
        print("No recommendations found")
        return
    
    print(f"\nAnalyzing {len(recommendations)} recommendations...")
    
    # Analyze each recommendation
    analyses = []
    for rec in recommendations:
        analysis = analyze_recommendation(rec)
        if analysis:
            analyses.append(analysis)
    
    print(f"Successfully analyzed {len(analyses)} recommendations")
    
    # Generate summary
    summary = generate_nlp_summary(analyses)
    
    # Print results
    print("\n" + "-" * 60)
    print("SENTIMENT ANALYSIS RESULTS")
    print("-" * 60)
    
    print(f"\nOverall Sentiment Distribution:")
    for sentiment, count in summary['sentiment_distribution'].items():
        pct = count / summary['total_recommendations'] * 100
        print(f"  {sentiment.capitalize()}: {count} ({pct:.1f}%)")
    
    print(f"\nAverage Sentiment Score: {summary['average_sentiment_score']}")
    print(f"  (Scale: -1 = very negative, 0 = neutral, +1 = very positive)")
    
    print(f"\nUrgency Distribution:")
    for urgency, count in summary['urgency_distribution'].items():
        pct = count / summary['total_recommendations'] * 100
        print(f"  {urgency.capitalize()}: {count} ({pct:.1f}%)")
    
    print("\n" + "-" * 60)
    print("ENTITY EXTRACTION RESULTS")
    print("-" * 60)
    
    print(f"\nPolicy Theme Frequency:")
    sorted_cats = sorted(summary['entity_category_frequency'].items(), key=lambda x: -x[1])
    for cat, count in sorted_cats:
        pct = count / summary['total_recommendations'] * 100
        print(f"  {cat.replace('_', ' ').title()}: {count} mentions ({pct:.1f}%)")
    
    print("\n" + "-" * 60)
    print("HIGH CONCERN AREAS")
    print("-" * 60)
    
    print(f"\nRecommendations with High Urgency + Negative Sentiment: {summary['high_concern_count']}")
    if summary['high_concern_departments']:
        print(f"\nTop Departments with Concerns:")
        for dept, count in list(summary['high_concern_departments'].items())[:10]:
            print(f"  {dept}: {count}")
    
    print("\n" + "-" * 60)
    print("MONETARY REFERENCES")
    print("-" * 60)
    
    print(f"\nRecommendations mentioning specific amounts: {summary['recommendations_with_monetary_refs']}")
    if summary['total_monetary_referenced'] > 0:
        total_bn = summary['total_monetary_referenced'] / 1_000_000_000
        print(f"Total value referenced: R{total_bn:.2f} billion")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    # Save detailed analyses
    analyses_path = output_dir / "nlp_analysis_detailed.json"
    with open(analyses_path, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, indent=2, default=str)
    print(f"\nDetailed analysis saved to: {analyses_path}")
    
    # Save summary
    summary_path = output_dir / "nlp_analysis_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"Summary saved to: {summary_path}")
    
    # Generate markdown report
    report_path = output_dir / "nlp_analysis_report.md"
    generate_markdown_report(summary, report_path)
    print(f"Markdown report saved to: {report_path}")
    
    return summary


def generate_markdown_report(summary, output_path):
    """Generate a markdown report of NLP analysis."""
    
    report = f"""# NLP Analysis of BRRR Recommendations

## Executive Summary

This analysis applies Natural Language Processing techniques to {summary['total_recommendations']:,} 
Budget Review and Recommendations Report (BRRR) submissions to identify:
- **Sentiment patterns** - Are recommendations expressing concerns or progress?
- **Urgency levels** - Which issues require immediate attention?
- **Policy themes** - What topics are most frequently addressed?
- **High concern areas** - Where do urgency and negative sentiment intersect?

---

## Sentiment Analysis

### Overall Distribution

| Sentiment | Count | Percentage |
|-----------|-------|------------|
"""
    
    for sentiment, count in summary['sentiment_distribution'].items():
        pct = count / summary['total_recommendations'] * 100
        report += f"| {sentiment.capitalize()} | {count:,} | {pct:.1f}% |\n"
    
    report += f"""
**Average Sentiment Score:** {summary['average_sentiment_score']} 
*(Scale: -1 = very negative, 0 = neutral, +1 = very positive)*

### Urgency Distribution

| Urgency Level | Count | Percentage |
|---------------|-------|------------|
"""
    
    for urgency, count in summary['urgency_distribution'].items():
        pct = count / summary['total_recommendations'] * 100
        report += f"| {urgency.capitalize()} | {count:,} | {pct:.1f}% |\n"
    
    report += f"""
---

## Policy Theme Analysis

Recommendations were analyzed for mentions of key policy themes:

| Theme | Mentions | % of Recommendations |
|-------|----------|---------------------|
"""
    
    sorted_cats = sorted(summary['entity_category_frequency'].items(), key=lambda x: -x[1])
    for cat, count in sorted_cats:
        pct = count / summary['total_recommendations'] * 100
        theme_name = cat.replace('_', ' ').title()
        report += f"| {theme_name} | {count:,} | {pct:.1f}% |\n"
    
    report += f"""
---

## High Concern Areas

Recommendations flagged as **both high urgency AND negative sentiment**: **{summary['high_concern_count']:,}**

These represent the most pressing issues identified in committee deliberations.

### Top Departments with Concerns

| Department | High Concern Count |
|------------|-------------------|
"""
    
    if summary['high_concern_departments']:
        for dept, count in list(summary['high_concern_departments'].items())[:10]:
            report += f"| {dept} | {count} |\n"
    
    report += f"""
---

## Monetary References

- Recommendations mentioning specific amounts: **{summary['recommendations_with_monetary_refs']:,}**
"""
    
    if summary['total_monetary_referenced'] > 0:
        total_bn = summary['total_monetary_referenced'] / 1_000_000_000
        report += f"- Total value referenced: **R{total_bn:.2f} billion**\n"
    
    report += """
---

## Methodology

### Sentiment Analysis
- **Positive indicators**: improve, enhance, progress, success, effective, etc.
- **Negative indicators**: concern, fail, inadequate, irregular, wasteful, etc.
- **Urgency indicators**: urgent, immediate, critical, must, imperative, etc.

### Entity Extraction
Key terms grouped into policy themes:
- **Fiscal**: budget, expenditure, revenue, deficit, appropriation
- **Governance**: accountability, transparency, audit, compliance
- **Service Delivery**: infrastructure, maintenance, performance, targets
- **Human Resources**: vacancy, staff, recruitment, capacity building
- **Financial Management**: procurement, supply chain, contracts
- **SOE**: state-owned enterprises, Eskom, Transnet, etc.
- **Social**: poverty, inequality, health, education, housing
- **Economic**: GDP, growth, investment, trade, productivity

---

*Generated using NLP analysis of BRRR recommendations data*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    main()
