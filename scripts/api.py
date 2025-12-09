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

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"

# Create FastAPI app
app = FastAPI(
    title="BRRR Recommendations API",
    description="Access 5,256 South African parliamentary recommendations (2015-2025)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# DATA LOADING
# =============================================================================

def load_json(filename: str):
    """Load JSON file from analysis directory"""
    path = ANALYSIS_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_recommendations():
    """Load recommendations (full or sample)"""
    data = load_json("recommendations.json")
    if data is None:
        data = load_json("recommendations_sample.json")
    return data or []


# Cache data at startup
RECOMMENDATIONS = load_recommendations()
COST_ESTIMATES = load_json("cost_estimates.json")
PROVINCIAL_DATA = load_json("provincial_analysis.json")
COMMITTEE_DATA = load_json("committee_performance.json")
TIME_SERIES = load_json("time_series_analysis.json")
NLP_DATA = load_json("nlp_analysis_summary.json")
OV_DATA = load_json("operation_vulindlela.json")


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
def root():
    """API information and available endpoints"""
    return {
        "name": "BRRR Recommendations API",
        "version": "1.0.0",
        "description": "South African Parliamentary Budget Recommendations (2015-2025)",
        "total_recommendations": len(RECOMMENDATIONS),
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
def get_recommendations(
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
    filtered = RECOMMENDATIONS
    
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
def get_recommendation(rec_id: int):
    """Get a single recommendation by index"""
    if rec_id < 0 or rec_id >= len(RECOMMENDATIONS):
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return RECOMMENDATIONS[rec_id]


@app.get("/sectors")
def get_sectors():
    """List all available sectors"""
    sectors = list(set(r.get('sector') for r in RECOMMENDATIONS if r.get('sector')))
    return {
        "sectors": sorted(sectors),
        "count": len(sectors)
    }


@app.get("/years")
def get_years():
    """List all available years"""
    years = list(set(r.get('year') for r in RECOMMENDATIONS if r.get('year')))
    return {
        "years": sorted(years),
        "range": f"{min(years)}-{max(years)}" if years else None
    }


@app.get("/stats")
def get_stats():
    """Get summary statistics"""
    sectors = {}
    years = {}
    categories = {}
    
    for r in RECOMMENDATIONS:
        sector = r.get('sector', 'unknown')
        year = str(r.get('year', 'unknown'))
        category = r.get('category', 'unknown')
        
        sectors[sector] = sectors.get(sector, 0) + 1
        years[year] = years.get(year, 0) + 1
        categories[category] = categories.get(category, 0) + 1
    
    return {
        "total_recommendations": len(RECOMMENDATIONS),
        "by_sector": sectors,
        "by_year": years,
        "by_category": categories,
        "nlp_summary": NLP_DATA if NLP_DATA else None
    }


@app.get("/search")
def search_recommendations(
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
    query = q.lower()
    results = []
    
    for i, r in enumerate(RECOMMENDATIONS):
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
    if not COST_ESTIMATES:
        raise HTTPException(status_code=404, detail="Cost data not available")
    return COST_ESTIMATES


@app.get("/provincial")
def get_provincial():
    """Get provincial mention analysis"""
    if not PROVINCIAL_DATA:
        raise HTTPException(status_code=404, detail="Provincial data not available")
    return PROVINCIAL_DATA


@app.get("/committee-performance")
def get_committee_performance():
    """Get committee actionability rankings"""
    if not COMMITTEE_DATA:
        raise HTTPException(status_code=404, detail="Committee data not available")
    return COMMITTEE_DATA


@app.get("/time-series")
def get_time_series():
    """Get trends over time"""
    if not TIME_SERIES:
        raise HTTPException(status_code=404, detail="Time series data not available")
    return TIME_SERIES


@app.get("/operation-vulindlela")
def get_operation_vulindlela():
    """Get Operation Vulindlela reform data"""
    if not OV_DATA:
        raise HTTPException(status_code=404, detail="Operation Vulindlela data not available")
    return OV_DATA


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
