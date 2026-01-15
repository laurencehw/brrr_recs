"""
Shared Utilities Module
=======================
Common utility functions used across analysis scripts.
"""

import json
from pathlib import Path
from typing import Dict, List, Union, Any
import pandas as pd
import numpy as np


# =============================================================================
# DATA LOADING
# =============================================================================

def get_analysis_dir() -> Path:
    """Get the path to the analysis directory."""
    return Path(__file__).parent.parent / "analysis"


def load_recommendations_json() -> List[Dict]:
    """
    Load BRRR recommendations as a list of dictionaries.

    Returns:
        List of recommendation dictionaries, or empty list if not found.
    """
    recs_path = get_analysis_dir() / "recommendations.json"

    if not recs_path.exists():
        # Try sample file (for Streamlit Cloud where full file is gitignored)
        recs_path = get_analysis_dir() / "recommendations_sample.json"

    if not recs_path.exists():
        print(f"Warning: No recommendations file found")
        return []

    with open(recs_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, list):
            return data
        return data.get('recommendations', [])


def load_recommendations_df() -> pd.DataFrame:
    """
    Load BRRR recommendations as a pandas DataFrame.

    Returns:
        DataFrame of recommendations, or empty DataFrame if not found.
    """
    data = load_recommendations_json()
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()


def load_json_file(filename: str) -> Dict:
    """
    Load a JSON file from the analysis directory.

    Args:
        filename: Name of the JSON file (e.g., 'nlp_analysis_summary.json')

    Returns:
        Dictionary with file contents, or empty dict if not found.
    """
    path = get_analysis_dir() / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_csv_file(filename: str) -> pd.DataFrame:
    """
    Load a CSV file from the analysis directory.

    Args:
        filename: Name of the CSV file (e.g., 'economic_context_annual.csv')

    Returns:
        DataFrame with file contents, or empty DataFrame if not found.
    """
    path = get_analysis_dir() / filename
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


# =============================================================================
# JSON SERIALIZATION HELPERS
# =============================================================================

def convert_for_json(obj: Any) -> Any:
    """
    Convert numpy/pandas types to JSON-serializable Python types.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    return obj


def save_json_file(data: Any, filename: str, indent: int = 2) -> Path:
    """
    Save data to a JSON file in the analysis directory.

    Args:
        data: Data to save (will be converted to JSON-serializable format)
        filename: Name of the output file
        indent: JSON indentation level

    Returns:
        Path to the saved file
    """
    output_dir = get_analysis_dir()
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=convert_for_json)

    return output_path


# =============================================================================
# TEXT PROCESSING HELPERS
# =============================================================================

def clean_text(text: str) -> str:
    """
    Clean and normalize text for analysis.

    Args:
        text: Raw text string

    Returns:
        Cleaned text string
    """
    if not text or not isinstance(text, str):
        return ""

    # Basic normalization
    text = text.strip()
    # Remove multiple spaces
    import re
    text = re.sub(r'\s+', ' ', text)
    return text


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (default 200)
        suffix: Suffix to add if truncated (default "...")

    Returns:
        Truncated text
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
