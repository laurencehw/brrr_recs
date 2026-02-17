"""
BRRR Recommendations API

A simple REST API to access South African parliamentary recommendations data.

Run locally: uvicorn scripts.api:app --reload
Deploy: Can be deployed to any ASGI server (Vercel, Railway, etc.)

Endpoints:
- GET /                     - API info
- GET /recommendations      - All recommendations (with filters)
- GET /recommendations/{id} - Single recommendation
- GET /sectors              - List of sectors
- GET /stats                - Summary statistics
- GET /cost-analysis        - Cost estimates
- GET /provincial           - Provincial analysis
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"

# Data storage (populated at startup)
_data_store: Dict[str, Any] = {}


# =============================================================================
# DATA LOADING
# =============================================================================

def load_json(filename: str):
    """Load JSON file from analysis directory, returning None on missing or malformed file."""
    path = ANALYSIS_DIR / filename
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_recommendations():
    """Load recommendations (full or sample)"""
    data = load_json("recommendations.json")
    if data is None:
        data = load_json("recommendations_sample.json")
    return data or []


def _load_all_data() -> Dict[str, Any]:
    """Load all data files into memory"""
    return {
        'recommendations': load_recommendations(),
        'cost_estimates': load_json("cost_estimates.json"),
        'provincial_data': load_json("provincial_analysis.json"),
        'committee_data': load_json("committee_performance.json"),
        'time_series': load_json("time_series_analysis.json"),
        'nlp_data': load_json("nlp_analysis_summary.json"),
        'ov_data': load_json("operation_vulindlela.json"),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup, cleanup on shutdown"""
    # Startup: load all data
    _data_store.update(_load_all_data())
    yield
    # Shutdown: clear data
    _data_store.clear()


# Create FastAPI app with lifespan
app = FastAPI(
    title="BRRR Recommendations API",
    description="Access 5,256 South African parliamentary recommendations (2015-2025)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS: read allowed origins from ALLOWED_ORIGINS env var (comma-separated).
# Defaults to "*" for local/dev use.  Set ALLOWED_ORIGINS in production.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["GET"],  # Read-only API
    allow_headers=["*"],
)


# Helper to access loaded data
def get_recommendations():
    return _data_store.get('recommendations', [])


def get_data(key: str):
    return _data_store.get(key)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
def root():
    """API information and available endpoints"""
    recommendations = get_recommendations()
    return {
        "name": "BRRR Recommendations API",
        "version": "1.0.0",
        "description": "South African Parliamentary Budget Recommendations (2015-2025)",
        "total_recommendations": len(recommendations),
        "endpoints": {
            "/recommendations": "Get all recommendations (supports filtering)",
            "/recommendations/{id}": "Get single recommendation by index",
            "/sectors": "List available sectors",
            "/years": "List available years",
            "/stats": "Summary statistics",
            "/cost-analysis": "Implementation vs inaction costs",
            "/provincial": "Provincial mention analysis",
            "/committee-performance": "Committee actionability rankings",
            "/time-series": "Trends over time",
            "/operation-vulindlela": "Executive reform priorities",
            "/search": "Full-text search"
        },
        "documentation": "/docs"
    }


@app.get("/recommendations")
def list_recommendations(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    year: Optional[int] = Query(None, description="Filter by year"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Skip first N results")
):
    """
    Get all recommendations with optional filters.

    - **sector**: energy, finance, infrastructure, labour, science_tech, trade
    - **year**: 2015-2025
    - **category**: Budget/Fiscal, Policy/Legislation, etc.
    - **limit**: Max results (default 100, max 1000)
    - **offset**: Pagination offset
    """
    recommendations = get_recommendations()
    filtered = recommendations

    if sector:
        filtered = [r for r in filtered if r.get('sector', '').lower() == sector.lower()]
    if year:
        filtered = [r for r in filtered if r.get('year') == year]
    if category:
        filtered = [r for r in filtered if category.lower() in r.get('category', '').lower()]

    total = len(filtered)
    results = filtered[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(results),
        "data": results
    }


@app.get("/recommendations/{rec_id}")
def get_recommendation_by_id(rec_id: int):
    """Get a single recommendation by index"""
    recommendations = get_recommendations()
    if rec_id < 0 or rec_id >= len(recommendations):
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendations[rec_id]


@app.get("/sectors")
def list_sectors():
    """List all available sectors"""
    recommendations = get_recommendations()
    sectors = list(set(r.get('sector') for r in recommendations if r.get('sector')))
    return {
        "sectors": sorted(sectors),
        "count": len(sectors)
    }


@app.get("/years")
def list_years():
    """List all available years"""
    recommendations = get_recommendations()
    years = list(set(r.get('year') for r in recommendations if r.get('year')))
    return {
        "years": sorted(years),
        "range": f"{min(years)}-{max(years)}" if years else None
    }


@app.get("/stats")
def get_stats():
    """Get summary statistics"""
    recommendations = get_recommendations()
    nlp_data = get_data('nlp_data')

    sectors = {}
    years = {}
    categories = {}

    for r in recommendations:
        sector = r.get('sector', 'unknown')
        year = str(r.get('year', 'unknown'))
        category = r.get('category', 'unknown')

        sectors[sector] = sectors.get(sector, 0) + 1
        years[year] = years.get(year, 0) + 1
        categories[category] = categories.get(category, 0) + 1

    return {
        "total_recommendations": len(recommendations),
        "by_sector": sectors,
        "by_year": years,
        "by_category": categories,
        "nlp_summary": nlp_data if nlp_data else None
    }


@app.get("/search")
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    sector: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Full-text search across recommendations.

    - **q**: Search terms (required, min 2 characters)
    - **sector**: Optional sector filter
    - **year**: Optional year filter
    """
    recommendations = get_recommendations()
    query = q.lower()
    results = []

    for i, r in enumerate(recommendations):
        text = r.get('recommendation', '').lower()
        if query in text:
            if sector and r.get('sector', '').lower() != sector.lower():
                continue
            if year and r.get('year') != year:
                continue
            results.append({**r, "id": i})
            if len(results) >= limit:
                break

    return {
        "query": q,
        "count": len(results),
        "data": results
    }


@app.get("/cost-analysis")
def get_cost_analysis():
    """Get implementation costs vs cost of inaction"""
    cost_estimates = get_data('cost_estimates')
    if not cost_estimates:
        raise HTTPException(status_code=404, detail="Cost data not available")
    return cost_estimates


@app.get("/provincial")
def get_provincial():
    """Get provincial mention analysis"""
    provincial_data = get_data('provincial_data')
    if not provincial_data:
        raise HTTPException(status_code=404, detail="Provincial data not available")
    return provincial_data


@app.get("/committee-performance")
def get_committee_performance():
    """Get committee actionability rankings"""
    committee_data = get_data('committee_data')
    if not committee_data:
        raise HTTPException(status_code=404, detail="Committee data not available")
    return committee_data


@app.get("/time-series")
def get_time_series():
    """Get trends over time"""
    time_series = get_data('time_series')
    if not time_series:
        raise HTTPException(status_code=404, detail="Time series data not available")
    return time_series


@app.get("/operation-vulindlela")
def get_operation_vulindlela():
    """Get Operation Vulindlela reform data"""
    ov_data = get_data('ov_data')
    if not ov_data:
        raise HTTPException(status_code=404, detail="Operation Vulindlela data not available")
    return ov_data


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
