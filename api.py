from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import geopandas as gpd
from pathlib import Path
from src.xml_exporter import export_to_xml

# --- הגדרת מבנה הנתונים (Pydantic Models) ---
class FeatureProperties(BaseModel):
    name: str
    priority: str
    resolution: str
    notes: Optional[str] = None  # Optional
    #If user wants to add a new field, do it here

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

# הגדרת נתיבים
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
    """
    קבלת נתונים מובנים ומעבר ל-XML
    """
    print("DEBUG: Payload data:", payload.model_dump())
    try:
        # Pydantic כבר תיקף שהנתונים תקינים לפני שהגענו לכאן
        data_dict = payload.model_dump()
        
        # 1. הפיכה ל-GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(data_dict["features"])
        
        # 2. שמירה
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