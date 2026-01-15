"""
Enhanced NLP Analysis for BRRR Recommendations
===============================================
Uses spaCy for entity extraction, BERTopic for topic modeling,
and sentence transformers for semantic similarity/deduplication.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# Check for optional dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm")

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")

try:
    from bertopic import BERTopic
    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    print("Warning: BERTopic not available. Install with: pip install bertopic")

# Import shared utilities
from utils import load_recommendations_json, save_json_file, convert_for_json


# =============================================================================
# DATA LOADING
# =============================================================================

def load_recommendations() -> List[Dict]:
    """Load the BRRR recommendations data."""
    return load_recommendations_json()


# =============================================================================
# SPACY ENTITY EXTRACTION
# =============================================================================

class SpacyAnalyzer:
    """Enhanced entity extraction using spaCy NLP."""

    def __init__(self):
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy is required. Install with: pip install spacy")

        # Load model (try medium first, then small)
        try:
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Downloading spaCy model...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.nlp = spacy.load("en_core_web_sm")

        # SA-specific entities to look for
        self.sa_orgs = {
            'eskom', 'transnet', 'prasa', 'denel', 'saa', 'sanral', 'petro sa',
            'treasury', 'national treasury', 'sarb', 'sars', 'nersa', 'icasa',
            'cogta', 'dffe', 'dmre', 'dtic', 'dalrrd', 'dbsa', 'idc', 'ppc',
            'parliament', 'portfolio committee', 'ncop', 'cabinet', 'presidency'
        }

        self.sa_places = {
            'gauteng', 'western cape', 'kwazulu-natal', 'kzn', 'eastern cape',
            'limpopo', 'mpumalanga', 'north west', 'northern cape', 'free state',
            'johannesburg', 'cape town', 'durban', 'pretoria', 'ethekwini',
            'tshwane', 'ekurhuleni', 'richards bay', 'saldanha', 'coega', 'ngqura'
        }

    def extract_entities(self, text: str) -> Dict:
        """Extract named entities from text using spaCy."""
        doc = self.nlp(text[:50000])  # Limit for performance

        entities = {
            'organizations': [],
            'persons': [],
            'money': [],
            'dates': [],
            'percentages': [],
            'locations': [],
            'sa_organizations': [],
            'sa_provinces': [],
            'laws_acts': []
        }

        text_lower = text.lower()

        # Standard NER
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'PERCENT':
                entities['percentages'].append(ent.text)
            elif ent.label_ in ('GPE', 'LOC'):
                entities['locations'].append(ent.text)

        # SA-specific entity detection
        for org in self.sa_orgs:
            if org in text_lower:
                entities['sa_organizations'].append(org.title())

        for place in self.sa_places:
            if place in text_lower:
                entities['sa_provinces'].append(place.title())

        # Detect South African legislation
        act_patterns = [
            r'(Public Finance Management Act|PFMA)',
            r'(Municipal Finance Management Act|MFMA)',
            r'(Division of Revenue Act|DORA)',
            r'(Preferential Procurement Policy Framework Act|PPPFA)',
            r'(Public Audit Act)',
            r'(Electricity Regulation Act|ERA)',
            r'(National Water Act)',
            r'(Skills Development Act)',
            r'(Labour Relations Act|LRA)',
            r'(Competition Act)',
            r'(Constitution|Bill of Rights)',
        ]
        for pattern in act_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['laws_acts'].extend([m if isinstance(m, str) else m[0] for m in matches])

        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def extract_key_phrases(self, text: str, n: int = 10) -> List[str]:
        """Extract key noun phrases from text."""
        doc = self.nlp(text[:50000])

        # Get noun chunks
        chunks = [chunk.text.lower() for chunk in doc.noun_chunks
                  if len(chunk.text) > 3 and not chunk.text.lower() in ['the', 'this', 'that', 'these', 'those']]

        # Count and return top n
        chunk_counts = Counter(chunks)
        return [phrase for phrase, _ in chunk_counts.most_common(n)]

    def analyze_sentiment_advanced(self, text: str) -> Dict:
        """Advanced sentiment analysis using linguistic features."""
        doc = self.nlp(text[:50000])

        # Count linguistic features
        negations = 0
        intensifiers = 0
        hedges = 0

        negation_words = {'not', 'no', 'never', 'neither', 'none', 'nobody', 'nothing', 'nowhere'}
        intensifier_words = {'very', 'extremely', 'highly', 'significantly', 'severely', 'critically', 'strongly'}
        hedge_words = {'may', 'might', 'could', 'possibly', 'perhaps', 'seemingly', 'apparently'}

        for token in doc:
            if token.text.lower() in negation_words:
                negations += 1
            elif token.text.lower() in intensifier_words:
                intensifiers += 1
            elif token.text.lower() in hedge_words:
                hedges += 1

        # Directive strength
        directive_strong = len(re.findall(r'\b(must|shall|will|require|mandate)\b', text, re.I))
        directive_medium = len(re.findall(r'\b(should|recommend|urge|encourage)\b', text, re.I))
        directive_weak = len(re.findall(r'\b(may|could|consider|note)\b', text, re.I))

        total_directives = directive_strong + directive_medium + directive_weak
        if total_directives > 0:
            directive_score = (directive_strong * 3 + directive_medium * 2 + directive_weak) / (total_directives * 3)
        else:
            directive_score = 0.5

        return {
            'negations': negations,
            'intensifiers': intensifiers,
            'hedges': hedges,
            'directive_strong': directive_strong,
            'directive_medium': directive_medium,
            'directive_weak': directive_weak,
            'directive_score': round(directive_score, 3),
            'certainty_score': round(1 - (hedges / max(len(doc), 1)) * 10, 3)
        }


# =============================================================================
# SEMANTIC SIMILARITY & DEDUPLICATION
# =============================================================================

class SemanticAnalyzer:
    """Semantic similarity analysis using sentence transformers."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers required. Install with: pip install sentence-transformers")

        print(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.texts = None

    def compute_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Compute embeddings for a list of texts."""
        print(f"Computing embeddings for {len(texts)} texts...")
        self.texts = texts
        self.embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
        return self.embeddings

    def find_similar(self, query: str, top_k: int = 10) -> List[Tuple[int, float, str]]:
        """Find most similar texts to a query."""
        if self.embeddings is None:
            raise ValueError("Call compute_embeddings first")

        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append((int(idx), float(similarities[idx]), self.texts[idx][:200]))

        return results

    def find_duplicates(self, threshold: float = 0.85) -> List[Tuple[int, int, float]]:
        """Find duplicate/near-duplicate texts based on similarity threshold."""
        if self.embeddings is None:
            raise ValueError("Call compute_embeddings first")

        print(f"Computing similarity matrix...")
        sim_matrix = cosine_similarity(self.embeddings)

        duplicates = []
        n = len(self.texts)
        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i, j] >= threshold:
                    duplicates.append((i, j, float(sim_matrix[i, j])))

        print(f"Found {len(duplicates)} duplicate pairs above threshold {threshold}")
        return duplicates

    def cluster_by_similarity(self, n_clusters: int = 20) -> Dict[int, List[int]]:
        """Cluster texts by semantic similarity."""
        if self.embeddings is None:
            raise ValueError("Call compute_embeddings first")

        from sklearn.cluster import KMeans

        print(f"Clustering into {n_clusters} groups...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(self.embeddings)

        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters[int(label)].append(idx)

        return dict(clusters)


# =============================================================================
# TOPIC MODELING
# =============================================================================

class TopicModeler:
    """Topic modeling using BERTopic."""

    def __init__(self):
        if not BERTOPIC_AVAILABLE:
            raise ImportError("BERTopic required. Install with: pip install bertopic")

        self.model = None
        self.topics = None
        self.probs = None

    def fit(self, texts: List[str], nr_topics: int = 20, min_topic_size: int = 10) -> Dict:
        """Fit topic model to texts."""
        print(f"Fitting BERTopic model on {len(texts)} documents...")

        self.model = BERTopic(
            language="english",
            nr_topics=nr_topics,
            min_topic_size=min_topic_size,
            verbose=True
        )

        self.topics, self.probs = self.model.fit_transform(texts)

        # Get topic info
        topic_info = self.model.get_topic_info()

        # Get representative words for each topic
        topic_words = {}
        for topic_id in topic_info['Topic'].unique():
            if topic_id != -1:  # Skip outlier topic
                words = self.model.get_topic(topic_id)
                topic_words[int(topic_id)] = [(w, round(s, 4)) for w, s in words[:10]]

        return {
            'n_topics': len(topic_words),
            'topic_info': topic_info.to_dict('records'),
            'topic_words': topic_words,
            'topic_assignments': [int(t) for t in self.topics],
            'outliers': int(sum(1 for t in self.topics if t == -1))
        }

    def get_topic_for_text(self, text: str) -> Tuple[int, float]:
        """Get the most likely topic for a new text."""
        if self.model is None:
            raise ValueError("Call fit first")

        topics, probs = self.model.transform([text])
        return int(topics[0]), float(probs[0])

    def visualize_topics(self) -> Optional[str]:
        """Generate topic visualization HTML."""
        if self.model is None:
            return None

        try:
            fig = self.model.visualize_topics()
            return fig.to_html()
        except Exception as e:
            print(f"Visualization failed: {e}")
            return None


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_enhanced_nlp_analysis(save_results: bool = True) -> Dict:
    """Run the complete enhanced NLP analysis pipeline."""
    print("=" * 70)
    print("ENHANCED NLP ANALYSIS")
    print("=" * 70)

    # Load data
    recommendations = load_recommendations()
    if not recommendations:
        print("No recommendations found")
        return {}

    texts = [r.get('recommendation', '') for r in recommendations]
    texts = [t for t in texts if t]  # Filter empty
    print(f"\nAnalyzing {len(texts)} recommendations...")

    results = {
        'total_analyzed': len(texts),
        'spacy_available': SPACY_AVAILABLE,
        'embeddings_available': EMBEDDINGS_AVAILABLE,
        'bertopic_available': BERTOPIC_AVAILABLE,
    }

    # 1. SpaCy Analysis
    if SPACY_AVAILABLE:
        print("\n" + "-" * 50)
        print("1. SPACY ENTITY EXTRACTION")
        print("-" * 50)

        spacy_analyzer = SpacyAnalyzer()

        all_entities = defaultdict(list)
        sample_analyses = []

        for i, text in enumerate(texts[:100]):  # Sample for speed
            entities = spacy_analyzer.extract_entities(text)
            sentiment = spacy_analyzer.analyze_sentiment_advanced(text)

            for key, values in entities.items():
                all_entities[key].extend(values)

            if i < 10:  # Save first 10 as samples
                sample_analyses.append({
                    'text': text[:200],
                    'entities': entities,
                    'sentiment': sentiment
                })

        # Aggregate entity frequencies
        entity_frequencies = {}
        for key, values in all_entities.items():
            entity_frequencies[key] = Counter(values).most_common(20)

        results['spacy_analysis'] = {
            'entity_frequencies': entity_frequencies,
            'sample_analyses': sample_analyses,
            'unique_sa_orgs': list(set(all_entities['sa_organizations'])),
            'unique_laws': list(set(all_entities['laws_acts']))
        }

        print(f"Extracted entities from {len(texts[:100])} recommendations")
        print(f"Found {len(set(all_entities['sa_organizations']))} unique SA organizations")
        print(f"Found {len(set(all_entities['laws_acts']))} unique laws/acts")

    # 2. Semantic Analysis
    if EMBEDDINGS_AVAILABLE:
        print("\n" + "-" * 50)
        print("2. SEMANTIC SIMILARITY ANALYSIS")
        print("-" * 50)

        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.compute_embeddings(texts[:1000])  # Limit for speed

        # Find duplicates
        duplicates = semantic_analyzer.find_duplicates(threshold=0.90)

        # Cluster
        clusters = semantic_analyzer.cluster_by_similarity(n_clusters=15)
        cluster_sizes = {k: len(v) for k, v in clusters.items()}

        results['semantic_analysis'] = {
            'duplicates_found': len(duplicates),
            'duplicate_pairs': duplicates[:50],  # Top 50
            'clusters': cluster_sizes,
            'largest_cluster': max(cluster_sizes.values()) if cluster_sizes else 0
        }

        print(f"Found {len(duplicates)} near-duplicate pairs")
        print(f"Clustered into {len(clusters)} groups")

    # 3. Topic Modeling
    if BERTOPIC_AVAILABLE:
        print("\n" + "-" * 50)
        print("3. TOPIC MODELING")
        print("-" * 50)

        topic_modeler = TopicModeler()
        topic_results = topic_modeler.fit(texts[:2000], nr_topics=15)  # Limit for speed

        results['topic_modeling'] = topic_results

        print(f"Discovered {topic_results['n_topics']} topics")
        print(f"Outliers: {topic_results['outliers']}")

    # Save results
    if save_results:
        output_path = save_json_file(results, "enhanced_nlp_analysis.json")
        print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    results = run_enhanced_nlp_analysis()

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    if results.get('spacy_analysis'):
        print(f"\nSpaCy: Found {len(results['spacy_analysis']['unique_sa_orgs'])} SA organizations")

    if results.get('semantic_analysis'):
        print(f"Semantic: Found {results['semantic_analysis']['duplicates_found']} duplicates")

    if results.get('topic_modeling'):
        print(f"Topics: Discovered {results['topic_modeling']['n_topics']} topics")
