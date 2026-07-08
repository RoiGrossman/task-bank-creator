from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import geopandas as gpd
from pathlib import Path
from src.xml_exporter import export_to_xml
from datetime import datetime, time

# Dataset definition
class FeatureProperties(BaseModel):
    name: str
    priority: str
    resolution: str
    scanAzimuth: Optional[str] = None # scanAzimuth is collected but not implemented in xml!
    dateRangeStart: datetime # dateRangeStart is collected but not implemented in xml!
    dateRangeEnd: datetime # dateRangeEnd is collected but not implemented in xml!
    timeInDayStart: Optional[time] = None # timeInDayStart is collected but not implemented in xml!
    timeInDayEnd: Optional[time] = None # timeInDayEnd is collected but not implemented in xml!
    viewAzMin: Optional[str] = None # viewAzMin is collected but not implemented in xml!
    viewAzMax: Optional[str] = None # viewAzMax is collected but not implemented in xml!
    satElevMin: Optional[str] = None # satElevMin is collected but not implemented in xml!
    satElevMax: Optional[str] = None # satElevMax is collected but not implemented in xml!

    # notes: Optional[str] = None  # Optional
    # Add new fields here if needed

class Feature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: FeatureProperties

class GeoJSONPayload(BaseModel):
    features: List[Feature]
# ---------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "web_interface" / "index.html"
EXPORT_DIR = BASE_DIR / "2-data" / "processed" / "xml_ready_taskfiles" / "manual_exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def get_index():
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="HTML file not found")
    return HTMLResponse(content=INDEX_FILE.read_text(encoding="utf-8"))

@app.post("/generate-xml")
async def generate_xml(payload: GeoJSONPayload):

    print("------------------------ Received Data ------------------------")
    print(payload.model_dump_json(indent=2))
    print("---------------------------------------------------------------")

    try:
        data_dict = payload.model_dump()
        gdf = gpd.GeoDataFrame.from_features(data_dict["features"])
        output_path = EXPORT_DIR / "manual_target.xml"
        export_to_xml(gdf, output_path)
        
        return FileResponse(
            path=output_path, 
            media_type='application/xml', 
            filename='manual_target.xml'
        )
    except Exception as e:
        print(f"Error during export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")