"""
Implementation Status Tracking System
=====================================
Track which recommendations have been implemented, cross-reference with
legislation, budget allocations, and annual reports.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd


# =============================================================================
# DATA LOADING
# =============================================================================

def load_recommendations() -> List[Dict]:
    """Load the BRRR recommendations data."""
    recs_path = Path(__file__).parent.parent / "analysis" / "recommendations.json"

    if not recs_path.exists():
        recs_path = Path(__file__).parent.parent / "analysis" / "recommendations_sample.json"

    if not recs_path.exists():
        return []

    with open(recs_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get('recommendations', [])


# =============================================================================
# IMPLEMENTATION STATUS MODEL
# =============================================================================

class ImplementationStatus:
    """Track implementation status of recommendations."""

    STATUSES = {
        'implemented': 'Fully implemented and verified',
        'partial': 'Partially implemented or in progress',
        'not_implemented': 'No evidence of implementation',
        'superseded': 'Replaced by newer policy/recommendation',
        'no_longer_relevant': 'Context has changed, no longer applicable',
        'unknown': 'Status cannot be determined'
    }

    def __init__(self):
        self.tracking_data = {}
        self.load_tracking_data()

    def load_tracking_data(self):
        """Load existing tracking data if available."""
        path = Path(__file__).parent.parent / "analysis" / "implementation_tracking.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.tracking_data = json.load(f)
        else:
            self.tracking_data = {
                'last_updated': None,
                'recommendations': {},
                'summary': {}
            }

    def save_tracking_data(self):
        """Save tracking data to file."""
        self.tracking_data['last_updated'] = datetime.now().isoformat()

        path = Path(__file__).parent.parent / "analysis" / "implementation_tracking.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.tracking_data, f, indent=2)

    def update_status(
        self,
        rec_id: str,
        status: str,
        evidence: str = "",
        source: str = "",
        notes: str = ""
    ):
        """Update implementation status for a recommendation."""
        if status not in self.STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {list(self.STATUSES.keys())}")

        self.tracking_data['recommendations'][rec_id] = {
            'status': status,
            'evidence': evidence,
            'source': source,
            'notes': notes,
            'updated_at': datetime.now().isoformat()
        }

    def get_status(self, rec_id: str) -> Optional[Dict]:
        """Get implementation status for a recommendation."""
        return self.tracking_data['recommendations'].get(rec_id)

    def get_summary(self) -> Dict:
        """Get summary statistics of implementation status."""
        status_counts = defaultdict(int)
        for rec_data in self.tracking_data['recommendations'].values():
            status_counts[rec_data['status']] += 1

        total = sum(status_counts.values())
        return {
            'total_tracked': total,
            'by_status': dict(status_counts),
            'implementation_rate': (
                (status_counts['implemented'] + status_counts['partial'] * 0.5) / total * 100
                if total > 0 else 0
            )
        }


# =============================================================================
# AUTO-DETECTION HEURISTICS
# =============================================================================

class ImplementationDetector:
    """
    Attempt to automatically detect implementation status based on:
    - Keyword patterns in subsequent years' reports
    - Cross-reference with known legislation
    - Budget allocation patterns
    """

    # Known implemented reforms (manually verified)
    KNOWN_IMPLEMENTATIONS = {
        'energy': [
            {'pattern': r'renewable.*(ipp|independent\s+power)', 'status': 'partial',
             'evidence': 'REIPPPP ongoing since 2011, bid windows 5-7 completed'},
            {'pattern': r'unbundl.*eskom', 'status': 'partial',
             'evidence': 'National Transmission Company of SA (NTCSA) established 2024'},
            {'pattern': r'nersa.*reform', 'status': 'partial',
             'evidence': 'ERA amendments in progress'},
        ],
        'finance': [
            {'pattern': r'e-?tender|central.*procurement', 'status': 'partial',
             'evidence': 'eTender portal exists but adoption incomplete'},
            {'pattern': r'pfma.*amendment', 'status': 'not_implemented',
             'evidence': 'No major PFMA amendments passed 2015-2025'},
            {'pattern': r'irregular.*expenditure.*consequence', 'status': 'not_implemented',
             'evidence': 'R300bn+ accumulated, limited consequence management'},
        ],
        'labour': [
            {'pattern': r'seta.*reform', 'status': 'partial',
             'evidence': 'NSDP 2030 launched, implementation ongoing'},
            {'pattern': r'skills\s+levy', 'status': 'partial',
             'evidence': 'Levies collected but disbursement challenges remain'},
        ],
        'infrastructure': [
            {'pattern': r'transnet.*reform', 'status': 'partial',
             'evidence': 'Private sector partnerships piloted at ports'},
            {'pattern': r'municipal.*infrastructure.*grant', 'status': 'partial',
             'evidence': 'MIG allocations continue but underspending persists'},
        ],
        'trade': [
            {'pattern': r'port.*efficiency|turnaround', 'status': 'partial',
             'evidence': 'Operation Vulindlela port reforms initiated'},
            {'pattern': r'one.*stop.*border', 'status': 'partial',
             'evidence': 'OSBP at Beitbridge piloted'},
        ],
        'science_tech': [
            {'pattern': r'spectrum.*allocation', 'status': 'implemented',
             'evidence': 'Spectrum auction completed March 2022'},
            {'pattern': r'broadband|connectivity', 'status': 'partial',
             'evidence': 'SA Connect ongoing but behind targets'},
        ]
    }

    def __init__(self):
        self.tracker = ImplementationStatus()

    def auto_detect_status(self, recommendation: Dict) -> Dict:
        """
        Attempt to automatically detect implementation status.
        Returns confidence score and reasoning.
        """
        text = recommendation.get('recommendation', '').lower()
        sector = recommendation.get('sector', '').lower()
        year = recommendation.get('year', 2020)

        result = {
            'detected_status': 'unknown',
            'confidence': 0.0,
            'reasoning': [],
            'matches': []
        }

        # Check against known implementations
        sector_patterns = self.KNOWN_IMPLEMENTATIONS.get(sector, [])
        for pattern_info in sector_patterns:
            if re.search(pattern_info['pattern'], text, re.IGNORECASE):
                result['detected_status'] = pattern_info['status']
                result['confidence'] = 0.7
                result['matches'].append({
                    'pattern': pattern_info['pattern'],
                    'evidence': pattern_info['evidence']
                })
                result['reasoning'].append(f"Matched known pattern: {pattern_info['evidence']}")

        # Age-based heuristics
        current_year = 2025
        age = current_year - year

        if age >= 5 and result['detected_status'] == 'unknown':
            # Old recommendations without known implementation likely not done
            result['detected_status'] = 'not_implemented'
            result['confidence'] = 0.3
            result['reasoning'].append(f"Recommendation is {age} years old with no known implementation")

        # Recurring theme detection
        recurring_themes = self._detect_recurring_themes(text)
        if recurring_themes:
            result['reasoning'].append(f"Recurring themes detected: {', '.join(recurring_themes)}")
            if result['confidence'] < 0.5:
                result['detected_status'] = 'not_implemented'
                result['confidence'] = 0.4

        return result

    def _detect_recurring_themes(self, text: str) -> List[str]:
        """Detect if recommendation relates to recurring unresolved issues."""
        recurring_patterns = {
            'irregular expenditure': r'irregular\s+(expenditure|spending)',
            'vacancy filling': r'vacanc(y|ies)',
            'consequence management': r'consequence\s+management',
            'procurement': r'procurement|tender(ing)?',
            'service delivery': r'service\s+delivery',
            'SOE governance': r'(soe|state.owned).*(governance|board)',
        }

        found = []
        for theme, pattern in recurring_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(theme)

        return found

    def bulk_detect(self, recommendations: List[Dict]) -> Dict:
        """Run auto-detection on all recommendations."""
        results = {
            'total': len(recommendations),
            'by_status': defaultdict(int),
            'high_confidence': [],
            'detections': []
        }

        for rec in recommendations:
            detection = self.auto_detect_status(rec)
            results['by_status'][detection['detected_status']] += 1

            if detection['confidence'] >= 0.5:
                results['high_confidence'].append({
                    'rec_id': rec.get('id'),
                    'text': rec.get('recommendation', '')[:200],
                    'status': detection['detected_status'],
                    'confidence': detection['confidence'],
                    'evidence': detection['matches']
                })

            results['detections'].append({
                'rec_id': rec.get('id'),
                'status': detection['detected_status'],
                'confidence': detection['confidence']
            })

        results['by_status'] = dict(results['by_status'])
        return results


# =============================================================================
# CROSS-REFERENCE WITH EXTERNAL DATA
# =============================================================================

class LegislationCrossReference:
    """Cross-reference recommendations with legislation and policy changes."""

    # Major legislation passed 2015-2025 (simplified)
    LEGISLATION_TIMELINE = [
        {'year': 2016, 'act': 'Protected Disclosures Amendment Act', 'sector': 'governance'},
        {'year': 2017, 'act': 'Traditional and Khoi-San Leadership Act', 'sector': 'governance'},
        {'year': 2018, 'act': 'Carbon Tax Act', 'sector': 'finance'},
        {'year': 2019, 'act': 'National Minimum Wage Act', 'sector': 'labour'},
        {'year': 2020, 'act': 'Disaster Management Act amendments (COVID)', 'sector': 'governance'},
        {'year': 2021, 'act': 'Economic Reconstruction and Recovery Plan', 'sector': 'economic'},
        {'year': 2022, 'act': 'Electricity Regulation Amendment Act', 'sector': 'energy'},
        {'year': 2022, 'act': 'Spectrum auction (ICASA)', 'sector': 'science_tech'},
        {'year': 2023, 'act': 'Electricity Amendment Bill (100MW threshold)', 'sector': 'energy'},
        {'year': 2024, 'act': 'National Transmission Company establishment', 'sector': 'energy'},
    ]

    def find_related_legislation(self, recommendation: Dict) -> List[Dict]:
        """Find legislation that might relate to a recommendation."""
        text = recommendation.get('recommendation', '').lower()
        sector = recommendation.get('sector', '').lower()
        year = recommendation.get('year', 2020)

        related = []
        for leg in self.LEGISLATION_TIMELINE:
            # Must be after recommendation year
            if leg['year'] <= year:
                continue

            # Check sector match
            sector_match = sector in leg.get('sector', '')

            # Check keyword match
            keywords = leg['act'].lower().split()
            keyword_match = any(kw in text for kw in keywords if len(kw) > 4)

            if sector_match or keyword_match:
                related.append({
                    **leg,
                    'match_type': 'sector' if sector_match else 'keyword'
                })

        return related


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_implementation_analysis(save_results: bool = True) -> Dict:
    """Run implementation status analysis."""
    print("=" * 70)
    print("IMPLEMENTATION STATUS ANALYSIS")
    print("=" * 70)

    recommendations = load_recommendations()
    if not recommendations:
        print("No recommendations found")
        return {}

    print(f"\nAnalyzing {len(recommendations)} recommendations...")

    detector = ImplementationDetector()
    leg_xref = LegislationCrossReference()

    # Run bulk detection
    detection_results = detector.bulk_detect(recommendations)

    # Cross-reference with legislation
    legislation_links = []
    for rec in recommendations[:500]:  # Sample for speed
        related_leg = leg_xref.find_related_legislation(rec)
        if related_leg:
            legislation_links.append({
                'rec_id': rec.get('id'),
                'text': rec.get('recommendation', '')[:100],
                'sector': rec.get('sector'),
                'year': rec.get('year'),
                'related_legislation': related_leg
            })

    results = {
        'analysis_date': datetime.now().isoformat(),
        'total_recommendations': len(recommendations),
        'detection_summary': {
            'by_status': detection_results['by_status'],
            'high_confidence_count': len(detection_results['high_confidence'])
        },
        'high_confidence_detections': detection_results['high_confidence'][:50],
        'legislation_cross_references': legislation_links[:50],
        'implementation_rate_estimate': (
            (detection_results['by_status'].get('implemented', 0) +
             detection_results['by_status'].get('partial', 0) * 0.5) /
            len(recommendations) * 100
        ),
        'methodology': {
            'description': 'Auto-detection based on keyword matching, known implementations, and age heuristics',
            'confidence_levels': {
                'high': '>= 0.7 - Matches known verified implementations',
                'medium': '0.5-0.7 - Partial matches or strong indicators',
                'low': '< 0.5 - Heuristic-based estimates only'
            },
            'limitations': [
                'Auto-detection cannot verify actual on-ground implementation',
                'Some implementations may occur without being captured',
                'Manual verification recommended for high-priority items'
            ]
        }
    }

    # Print summary
    print("\n" + "-" * 50)
    print("DETECTION SUMMARY")
    print("-" * 50)
    for status, count in detection_results['by_status'].items():
        pct = count / len(recommendations) * 100
        print(f"  {status}: {count} ({pct:.1f}%)")

    print(f"\nHigh-confidence detections: {len(detection_results['high_confidence'])}")
    print(f"Legislation cross-references found: {len(legislation_links)}")
    print(f"Estimated implementation rate: {results['implementation_rate_estimate']:.1f}%")

    # Save results
    if save_results:
        output_dir = Path(__file__).parent.parent / "analysis"
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / "implementation_analysis.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    results = run_implementation_analysis()
