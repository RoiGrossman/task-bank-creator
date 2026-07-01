from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import geopandas as gpd
import os
from src.xml_exporter import export_to_xml
from pathlib import Path


# Initialize the API
app = FastAPI()

# Enable CORS to allow the frontend (HTML) to communicate with the backend
# Don't release to the web!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_index():
    """
    Serves the frontend HTML file.
    """
    with open("web_interface/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

EXPORT_DIR = Path.cwd() / "2-data" / "processed" / "xml_ready_taskfiles" / "manual_exports"
EXPORT_DIR.mkdir(exist_ok=True)


@app.post("/generate-xml")
async def generate_xml(request: Request):
    """
    Receives GeoJSON data from the frontend, converts it to XML, 
    and returns the file for download.
    """
    # 1. Get the JSON data from the request
    data = await request.json()

    #Polygon exist validation
    features = data.get("features", [])
    if not features or not features[0].get("geometry"):
        raise HTTPException(status_code=400, detail="Error in data inputs")

    # Print data to terminalwindow
    print("DEBUG DATA:", data)
    
    # 2. Convert the features to a GeoDataFrame
    # We assume 'features' is a key in the GeoJSON object
    gdf = gpd.GeoDataFrame.from_features(data["features"])
    
    # 3. Set the output path
    output_filename = EXPORT_DIR / "manual_target.xml"
    
    # 4. Run the export logic
    export_to_xml(gdf, output_filename)
    
    # 5. Return the file to the user
    return FileResponse(output_filename, media_type='application/xml', filename='manual_target.xml')