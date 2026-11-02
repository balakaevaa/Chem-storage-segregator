import asyncio
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.classifier import classify_chemical
from app.compatibility_engine import analyze_inventory
from app.pubchem_client import fetch_chemical_data

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="ChemSegregate - GHS Chemical Compatibility & Storage Segregator",
    description="Free tool for laboratory chemical compatibility matrices and OSHA/TRGS 510 cabinet segregation.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class AnalyzeRequest(BaseModel):
    queries: List[str] = Field(..., min_length=1, max_length=25, description="List of CAS numbers or chemical names")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "chem-storage-segregator"}


@app.post("/api/analyze")
async def analyze_chemicals(payload: AnalyzeRequest):
    cleaned_queries = [q.strip() for q in payload.queries if q.strip()]
    if not cleaned_queries:
        raise HTTPException(status_code=400, detail="Please provide at least one valid CAS number or chemical name.")

    # Deduplicate while preserving order
    unique_queries = list(dict.fromkeys(cleaned_queries))[:20]

    # Fetch chemical profiles concurrently
    raw_profiles = await asyncio.gather(*(fetch_chemical_data(q) for q in unique_queries))

    classified_list = []
    for profile in raw_profiles:
        classification = classify_chemical(profile["name"], profile["h_codes"])
        classified_list.append({
            **profile,
            **classification
        })

    result = analyze_inventory(classified_list)
    return result