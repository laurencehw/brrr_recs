"""
Political Feasibility Scoring System
====================================
Enhanced scoring framework that considers political economy factors,
stakeholder alignment, and implementation dependencies.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

# Import shared utilities
from utils import load_recommendations_json, load_json_file, save_json_file


# =============================================================================
# DATA LOADING
# =============================================================================

def load_recommendations() -> List[Dict]:
    """Load the BRRR recommendations data."""
    return load_recommendations_json()


def load_operation_vulindlela() -> Dict:
    """Load Operation Vulindlela data for alignment checking."""
    return load_json_file("operation_vulindlela.json")


# =============================================================================
# POLITICAL FEASIBILITY FACTORS
# =============================================================================

class PoliticalFeasibilityScorer:
    """
    Score recommendations based on political feasibility factors.

    Factors considered:
    1. Executive alignment (matches OV priorities)
    2. Legislative complexity (needs new laws vs administrative)
    3. Inter-departmental coordination requirements
    4. Stakeholder opposition likelihood
    5. Public support indicators
    6. Fiscal implications
    7. Time horizon
    """

    # Weights for each factor (sum to 1.0)
    WEIGHTS = {
        'executive_alignment': 0.20,
        'legislative_complexity': 0.15,
        'coordination_complexity': 0.15,
        'stakeholder_opposition': 0.15,
        'public_support': 0.10,
        'fiscal_implications': 0.15,
        'time_horizon': 0.10
    }

    # Patterns indicating different feasibility levels
    PATTERNS = {
        'requires_legislation': [
            r'amend(ment)?\s+(act|law|legislation|bill)',
            r'(new|draft|pass)\s+(act|law|legislation|bill)',
            r'legislative\s+(change|amendment|reform)',
            r'(repeal|enact)',
        ],
        'administrative_only': [
            r'(review|improve|strengthen|enhance)\s+(process|procedure|guideline)',
            r'(develop|implement|establish)\s+(policy|guideline|framework|protocol)',
            r'(ensure|require)\s+(compliance|reporting|monitoring)',
            r'(expedite|fast.?track|accelerate)\s+approval',
        ],
        'inter_departmental': [
            r'inter.?department(al)?',
            r'cross.?sector(al)?',
            r'coordinat(e|ion|ed)\s+with',
            r'collaborat(e|ion|ive)',
            r'(multiple|various)\s+(department|ministr)',
            r'whole.?of.?government',
        ],
        'stakeholder_opposition': [
            r'(union|labour|organized\s+labour)',
            r'(private\s+sector|business|industry)\s+(opposition|resistance)',
            r'vested\s+interest',
            r'(monopol|cartel|oligopol)',
            r'(rent.?seek|capture|corrupt)',
            r'(tender.?preneur|politically\s+connected)',
        ],
        'high_public_support': [
            r'(job|employment|unemploy)',
            r'(service\s+delivery|basic\s+service)',
            r'(electricity|water|sanitation|housing)',
            r'(education|health|safety)',
            r'(cost\s+of\s+living|afford)',
            r'(poverty|inequal)',
        ],
        'high_cost': [
            r'R\s?\d+\s*(billion|bn)',
            r'significant\s+(invest|fund|capital)',
            r'major\s+(infrastructure|capital)',
            r'(multi.?year|long.?term)\s+fund',
        ],
        'low_cost': [
            r'(no|minimal|low)\s+(cost|budget)',
            r'cost.?neutral',
            r'(administrative|regulatory)\s+(change|reform)',
            r'(already|existing)\s+(fund|budget|appropriat)',
        ],
        'quick_implementation': [
            r'immediate(ly)?',
            r'(within|next)\s+\d+\s+(day|week|month)',
            r'short.?term',
            r'(expedite|fast.?track|urgent)',
        ],
        'long_term': [
            r'(medium|long).?term',
            r'(multi.?year|phased)',
            r'\d+\s*year\s*(plan|program|horizon)',
            r'(structural|fundamental)\s+reform',
        ]
    }

    # Operation Vulindlela priority areas (for alignment scoring)
    OV_PRIORITIES = {
        'energy': ['electricity', 'renewable', 'ipp', 'eskom', 'grid', 'generation', 'transmission'],
        'logistics': ['port', 'rail', 'transnet', 'freight', 'logistics', 'export'],
        'water': ['water', 'sanitation', 'reservoir', 'dam', 'municipal'],
        'digital': ['spectrum', 'broadband', 'digital', 'connectivity', '5g'],
        'visa': ['visa', 'tourism', 'immigration', 'e-visa'],
        'green_economy': ['green', 'climate', 'carbon', 'renewable', 'just transition']
    }

    def __init__(self):
        self.ov_data = load_operation_vulindlela()

    def score_recommendation(self, rec: Dict) -> Dict:
        """Calculate political feasibility score for a recommendation."""
        text = rec.get('recommendation', '').lower()
        sector = rec.get('sector', '').lower()

        scores = {}

        # 1. Executive Alignment (higher = more aligned)
        scores['executive_alignment'] = self._score_executive_alignment(text, sector)

        # 2. Legislative Complexity (higher = simpler/easier)
        scores['legislative_complexity'] = self._score_legislative_complexity(text)

        # 3. Coordination Complexity (higher = simpler/easier)
        scores['coordination_complexity'] = self._score_coordination_complexity(text)

        # 4. Stakeholder Opposition (higher = less opposition)
        scores['stakeholder_opposition'] = self._score_stakeholder_opposition(text)

        # 5. Public Support (higher = more support)
        scores['public_support'] = self._score_public_support(text)

        # 6. Fiscal Implications (higher = lower cost/easier to fund)
        scores['fiscal_implications'] = self._score_fiscal_implications(text)

        # 7. Time Horizon (higher = quicker implementation)
        scores['time_horizon'] = self._score_time_horizon(text)

        # Calculate weighted total
        total_score = sum(
            scores[factor] * weight
            for factor, weight in self.WEIGHTS.items()
        )

        return {
            'factor_scores': scores,
            'total_score': round(total_score, 3),
            'feasibility_level': self._get_feasibility_level(total_score),
            'key_barriers': self._identify_barriers(scores),
            'key_enablers': self._identify_enablers(scores)
        }

    def _score_executive_alignment(self, text: str, sector: str) -> float:
        """Score alignment with Operation Vulindlela priorities."""
        score = 0.5  # Neutral baseline

        # Check OV priority area matches
        for area, keywords in self.OV_PRIORITIES.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches >= 2:
                score += 0.15
            elif matches >= 1:
                score += 0.08

        # Sector alignment bonus
        ov_sectors = ['energy', 'infrastructure', 'trade', 'science_tech']
        if any(s in sector for s in ov_sectors):
            score += 0.1

        return min(1.0, max(0.0, score))

    def _score_legislative_complexity(self, text: str) -> float:
        """Score based on legislative requirements (1=easy, 0=hard)."""
        requires_leg = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['requires_legislation']
        )
        admin_only = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['administrative_only']
        )

        if requires_leg:
            return 0.2  # Hard - needs legislation
        elif admin_only:
            return 0.9  # Easy - administrative only
        else:
            return 0.5  # Uncertain

    def _score_coordination_complexity(self, text: str) -> float:
        """Score coordination requirements (1=simple, 0=complex)."""
        inter_dept = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['inter_departmental']
        )

        if inter_dept:
            return 0.3  # Requires coordination
        else:
            return 0.7  # Single department likely

    def _score_stakeholder_opposition(self, text: str) -> float:
        """Score likelihood of stakeholder opposition (1=no opposition, 0=strong opposition)."""
        opposition_indicators = sum(
            1 for p in self.PATTERNS['stakeholder_opposition']
            if re.search(p, text, re.I)
        )

        if opposition_indicators >= 2:
            return 0.2  # Strong opposition likely
        elif opposition_indicators == 1:
            return 0.4  # Some opposition
        else:
            return 0.7  # Low opposition expected

    def _score_public_support(self, text: str) -> float:
        """Score public support likelihood (1=high support, 0=low support)."""
        support_indicators = sum(
            1 for p in self.PATTERNS['high_public_support']
            if re.search(p, text, re.I)
        )

        if support_indicators >= 3:
            return 0.9  # High public interest
        elif support_indicators >= 1:
            return 0.7  # Moderate public interest
        else:
            return 0.5  # Neutral

    def _score_fiscal_implications(self, text: str) -> float:
        """Score fiscal feasibility (1=easy to fund, 0=expensive)."""
        high_cost = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['high_cost']
        )
        low_cost = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['low_cost']
        )

        if high_cost:
            return 0.2  # Expensive
        elif low_cost:
            return 0.9  # Cheap/funded
        else:
            return 0.5  # Uncertain

    def _score_time_horizon(self, text: str) -> float:
        """Score implementation timeline (1=quick, 0=slow)."""
        quick = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['quick_implementation']
        )
        long_term = any(
            re.search(p, text, re.I)
            for p in self.PATTERNS['long_term']
        )

        if quick:
            return 0.9  # Quick win
        elif long_term:
            return 0.3  # Long-term
        else:
            return 0.5  # Medium-term

    def _get_feasibility_level(self, score: float) -> str:
        """Convert score to feasibility level."""
        if score >= 0.7:
            return 'HIGH'
        elif score >= 0.5:
            return 'MEDIUM'
        elif score >= 0.3:
            return 'LOW'
        else:
            return 'VERY_LOW'

    def _identify_barriers(self, scores: Dict) -> List[str]:
        """Identify key barriers based on low-scoring factors."""
        barriers = []
        threshold = 0.4

        if scores['legislative_complexity'] < threshold:
            barriers.append('Requires legislative change')
        if scores['coordination_complexity'] < threshold:
            barriers.append('Requires inter-departmental coordination')
        if scores['stakeholder_opposition'] < threshold:
            barriers.append('Likely stakeholder opposition')
        if scores['fiscal_implications'] < threshold:
            barriers.append('High implementation cost')
        if scores['time_horizon'] < threshold:
            barriers.append('Long implementation timeline')

        return barriers

    def _identify_enablers(self, scores: Dict) -> List[str]:
        """Identify key enablers based on high-scoring factors."""
        enablers = []
        threshold = 0.7

        if scores['executive_alignment'] >= threshold:
            enablers.append('Aligned with Executive priorities')
        if scores['legislative_complexity'] >= threshold:
            enablers.append('Administrative change only')
        if scores['public_support'] >= threshold:
            enablers.append('High public support likely')
        if scores['fiscal_implications'] >= threshold:
            enablers.append('Low/no additional funding needed')
        if scores['time_horizon'] >= threshold:
            enablers.append('Quick implementation possible')

        return enablers


# =============================================================================
# DEPENDENCY MAPPING
# =============================================================================

class DependencyMapper:
    """Map dependencies between recommendations."""

    # Known dependency patterns
    DEPENDENCY_PATTERNS = {
        'requires_legislation': {
            'eskom_unbundling': [
                r'unbundl.*eskom',
                r'transmission.*company',
                r'generation.*separation'
            ],
            'procurement_reform': [
                r'central.*procurement',
                r'e-?tender.*platform',
                r'pppfa.*amendment'
            ],
            'labour_reform': [
                r'labour.*law.*amend',
                r'section\s*189',
                r'retrenchment.*process'
            ]
        },
        'requires_capacity': {
            'municipal_finance': [
                r'municipal.*capacity',
                r'mfma.*implement',
                r'financial.*management.*training'
            ],
            'infrastructure_delivery': [
                r'infrastructure.*unit',
                r'project.*management',
                r'engineering.*capacity'
            ]
        },
        'requires_political_will': {
            'consequence_management': [
                r'consequence.*management',
                r'disciplinary.*action',
                r'accountability'
            ],
            'soe_governance': [
                r'soe.*board',
                r'political.*appointment',
                r'cadre.*deployment'
            ]
        }
    }

    def find_dependencies(self, recommendation: Dict) -> List[Dict]:
        """Find what a recommendation depends on."""
        text = recommendation.get('recommendation', '').lower()
        dependencies = []

        for category, patterns in self.DEPENDENCY_PATTERNS.items():
            for dep_name, dep_patterns in patterns.items():
                for pattern in dep_patterns:
                    if re.search(pattern, text, re.I):
                        dependencies.append({
                            'dependency_type': category,
                            'dependency_name': dep_name,
                            'pattern_matched': pattern
                        })
                        break  # Only add once per dependency

        return dependencies

    def build_dependency_graph(self, recommendations: List[Dict]) -> Dict:
        """Build a graph of recommendation dependencies."""
        graph = {
            'nodes': [],
            'edges': []
        }

        for i, rec in enumerate(recommendations):
            graph['nodes'].append({
                'id': i,
                'label': rec.get('recommendation', '')[:50],
                'sector': rec.get('sector'),
                'year': rec.get('year')
            })

            deps = self.find_dependencies(rec)
            for dep in deps:
                graph['edges'].append({
                    'from': i,
                    'to': dep['dependency_name'],
                    'type': dep['dependency_type']
                })

        return graph


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_feasibility_analysis(save_results: bool = True) -> Dict:
    """Run political feasibility analysis on all recommendations."""
    print("=" * 70)
    print("POLITICAL FEASIBILITY ANALYSIS")
    print("=" * 70)

    recommendations = load_recommendations()
    if not recommendations:
        print("No recommendations found")
        return {}

    print(f"\nAnalyzing {len(recommendations)} recommendations...")

    scorer = PoliticalFeasibilityScorer()
    mapper = DependencyMapper()

    # Score all recommendations
    scored_recommendations = []
    feasibility_dist = defaultdict(int)
    barrier_counts = defaultdict(int)
    enabler_counts = defaultdict(int)

    for rec in recommendations:
        scores = scorer.score_recommendation(rec)
        feasibility_dist[scores['feasibility_level']] += 1

        for barrier in scores['key_barriers']:
            barrier_counts[barrier] += 1
        for enabler in scores['key_enablers']:
            enabler_counts[enabler] += 1

        scored_recommendations.append({
            'id': rec.get('id'),
            'sector': rec.get('sector'),
            'year': rec.get('year'),
            'text': rec.get('recommendation', '')[:200],
            **scores
        })

    # Find high feasibility recommendations
    high_feasibility = [r for r in scored_recommendations if r['feasibility_level'] == 'HIGH']
    high_feasibility.sort(key=lambda x: x['total_score'], reverse=True)

    # Find dependencies
    dep_graph = mapper.build_dependency_graph(recommendations[:500])

    results = {
        'total_analyzed': len(recommendations),
        'feasibility_distribution': dict(feasibility_dist),
        'top_barriers': dict(sorted(barrier_counts.items(), key=lambda x: -x[1])[:10]),
        'top_enablers': dict(sorted(enabler_counts.items(), key=lambda x: -x[1])[:10]),
        'high_feasibility_recommendations': high_feasibility[:50],
        'average_score': round(sum(r['total_score'] for r in scored_recommendations) / len(scored_recommendations), 3),
        'dependency_analysis': {
            'nodes_with_dependencies': sum(1 for n in dep_graph['edges']),
            'dependency_types': defaultdict(int)
        },
        'methodology': {
            'factors': list(scorer.WEIGHTS.keys()),
            'weights': scorer.WEIGHTS,
            'scoring_range': '0-1 for each factor, weighted total',
            'feasibility_thresholds': {
                'HIGH': '>= 0.7',
                'MEDIUM': '0.5-0.7',
                'LOW': '0.3-0.5',
                'VERY_LOW': '< 0.3'
            }
        }
    }

    # Count dependency types
    for edge in dep_graph['edges']:
        results['dependency_analysis']['dependency_types'][edge['type']] += 1
    results['dependency_analysis']['dependency_types'] = dict(results['dependency_analysis']['dependency_types'])

    # Print summary
    print("\n" + "-" * 50)
    print("FEASIBILITY DISTRIBUTION")
    print("-" * 50)
    for level, count in sorted(feasibility_dist.items()):
        pct = count / len(recommendations) * 100
        print(f"  {level}: {count} ({pct:.1f}%)")

    print(f"\nAverage feasibility score: {results['average_score']:.3f}")
    print(f"High feasibility recommendations: {len(high_feasibility)}")

    print("\n" + "-" * 50)
    print("TOP BARRIERS")
    print("-" * 50)
    for barrier, count in list(results['top_barriers'].items())[:5]:
        print(f"  {barrier}: {count}")

    print("\n" + "-" * 50)
    print("TOP ENABLERS")
    print("-" * 50)
    for enabler, count in list(results['top_enablers'].items())[:5]:
        print(f"  {enabler}: {count}")

    # Save results
    if save_results:
        output_path = save_json_file(results, "feasibility_analysis.json")
        print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    results = run_feasibility_analysis()
