"""
Simplified main application for Kubernetes deployment.
This version focuses on basic functionality without heavy ML dependencies.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from datetime import datetime
from typing import Dict, Any

# Simple in-memory storage for demo
sanctions_data = [
    {"name": "Osama Bin Laden", "type": "person", "country": "Saudi Arabia"},
    {"name": "Maria Garcia", "type": "person", "country": "Mexico"},
    {"name": "John Smith", "type": "person", "country": "USA"},
]

screening_results = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🚀 Starting Sanctions Screening Platform (K8s Version)...")
    yield
    print("🛑 Shutting down Sanctions Screening Platform...")

# Create FastAPI app
app = FastAPI(
    title="Sanctions Screening Platform",
    description="A production-quality sanctions screening platform",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface."""
    try:
        with open("app/static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>Sanctions Screening Platform</title></head>
            <body>
                <h1>Sanctions Screening Platform</h1>
                <p>Platform is running successfully!</p>
                <p><a href="/health">Health Check</a></p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sanctions-screening-platform",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "environment": "kubernetes"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return {
        "sanctions_screening_total": len(screening_results),
        "sanctions_list_size": len(sanctions_data),
        "uptime_seconds": 0  # Could be calculated from start time
    }

@app.post("/api/v1/screen")
async def screen_entity(entity_data: Dict[str, Any]):
    """Screen a single entity against sanctions lists."""
    try:
        entity_name = entity_data.get("name", "").lower()
        
        # Simple exact match screening
        matches = []
        for sanction in sanctions_data:
            if entity_name == sanction["name"].lower():
                matches.append({
                    "sanction_name": sanction["name"],
                    "match_type": "exact",
                    "similarity_score": 1.0,
                    "risk_score": 1.0
                })
        
        # Calculate overall risk
        overall_risk = 1.0 if matches else 0.0
        decision = "block" if overall_risk >= 0.8 else "clear"
        status = "blocked" if decision == "block" else "approved"
        
        result = {
            "entity": entity_data,
            "overall_risk_score": overall_risk,
            "decision": decision,
            "status": status,
            "matches": matches,
            "screening_timestamp": datetime.utcnow()
        }
        
        screening_results.append(result)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/entities")
async def get_entities():
    """Get all screened entities."""
    return {"entities": screening_results}

@app.get("/api/v1/sanctions")
async def get_sanctions():
    """Get sanctions list."""
    return {"sanctions": sanctions_data}

@app.get("/analytics/screenings")
async def get_analytics():
    """Get screening analytics."""
    total = len(screening_results)
    approved = len([r for r in screening_results if r["status"] == "approved"])
    blocked = len([r for r in screening_results if r["status"] == "blocked"])
    
    return {
        "total_screenings": total,
        "approved_count": approved,
        "blocked_count": blocked,
        "pending_count": 0,
        "average_risk_score": sum(r["overall_risk_score"] for r in screening_results) / total if total > 0 else 0,
        "screening_by_type": {"single": total},
        "risk_distribution": {
            "low": len([r for r in screening_results if r["overall_risk_score"] < 0.3]),
            "medium": len([r for r in screening_results if 0.3 <= r["overall_risk_score"] < 0.7]),
            "high": len([r for r in screening_results if r["overall_risk_score"] >= 0.7])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
