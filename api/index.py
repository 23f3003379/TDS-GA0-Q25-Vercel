from typing import Any, Dict, List
 
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
 
app = FastAPI()
 
# CORS: allow POST (and the OPTIONS preflight) from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Telemetry embedded in the code (serverless functions cannot rely on local files):
# (region, latency_ms, uptime_pct)
DATA = [
    ("apac", 208.44, 98.236),
    ("apac", 208.08, 97.865),
    ("apac", 126.33, 98.348),
    ("apac", 166.99, 97.889),
    ("apac", 183.81, 97.431),
    ("apac", 119.16, 98.607),
    ("apac", 121.21, 98.246),
    ("apac", 121.55, 99.402),
    ("apac", 146.79, 98.351),
    ("apac", 128.41, 98.475),
    ("apac", 174.21, 98.858),
    ("apac", 136.05, 98.176),
    ("emea", 118.46, 99.027),
    ("emea", 113.2, 98.583),
    ("emea", 125.4, 97.774),
    ("emea", 187.99, 97.243),
    ("emea", 222.22, 97.82),
    ("emea", 193.84, 98.324),
    ("emea", 164.54, 98.027),
    ("emea", 222.51, 99.201),
    ("emea", 221.41, 97.468),
    ("emea", 203.99, 98.018),
    ("emea", 151.11, 99.18),
    ("emea", 119.09, 99.416),
    ("amer", 195.46, 98.928),
    ("amer", 143.09, 99.409),
    ("amer", 127.7, 99.267),
    ("amer", 124.05, 98.737),
    ("amer", 115.04, 98.694),
    ("amer", 213.34, 99.089),
    ("amer", 220.32, 99.131),
    ("amer", 230.88, 98.854),
    ("amer", 209.92, 99.339),
    ("amer", 225.61, 98.789),
    ("amer", 182.53, 97.686),
    ("amer", 119.69, 98.932)
]
 
 
def percentile(values: List[float], q: float) -> float:
    """Linear-interpolation percentile (same as numpy's default)."""
    s = sorted(values)
    k = (len(s) - 1) * q / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)
 
 
def compute(regions: List[str], threshold: float) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for region in regions:
        rows = [r for r in DATA if r[0] == str(region).lower()]
        if not rows:
            out[region] = {"avg_latency": None, "p95_latency": None, "avg_uptime": None, "breaches": 0}
            continue
        lat = [r[1] for r in rows]
        up = [r[2] for r in rows]
        out[region] = {
            "avg_latency": round(sum(lat) / len(lat), 4),
            "p95_latency": round(percentile(lat, 95), 4),
            "avg_uptime": round(sum(up) / len(up), 4),
            "breaches": sum(1 for x in lat if x > threshold),
        }
    return out
 
 
async def handle(request: Request) -> Dict[str, Any]:
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))
    per_region = compute(regions, threshold)
    # per-region keys at the top level, plus the same data under "regions"
    return {**per_region, "regions": per_region}
 
 
# Catch-all routes: whatever path Vercel passes to the function (/, /api, /api/index ...)
@app.post("/")
@app.post("/{full_path:path}")
async def any_post(request: Request, full_path: str = ""):
    return await handle(request)
 
 
@app.get("/")
@app.get("/{full_path:path}")
def any_get(full_path: str = ""):
    return {"message": "POST {\"regions\": [...], \"threshold_ms\": 180} to this endpoint"}
 
@app.get("/")
def root_get():
    return {"message": "POST {\"regions\": [...], \"threshold_ms\": 180} to this endpoint"}
