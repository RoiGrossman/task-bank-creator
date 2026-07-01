import sys
import geopandas as gpd
from pathlib import Path

# Define base path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import the export function from src
from src.xml_exporter import export_to_xml

def process_shapefile_to_xml(shp_path):
    path = Path(shp_path)
    
    if not path.exists():
        print(f"Error: File not found at {path}")
        return

    print(f"Loading shapefile: {path.name}")
    gdf = gpd.read_file(path)
    
    # Feasibility check
    if len(gdf) == 0:
        print("CRITICAL: File is empty. No XML created.")
        return
        
    required = ['id', 'priority']
    missing = [col for col in required if col not in gdf.columns]
    if missing:
        print(f"CRITICAL: Missing columns in file: {missing}")
        return

    # Define output path (in the same directiry)
    output_xml = path.with_suffix(".xml")
    
    # Export 
    export_to_xml(gdf, str(output_xml))
    print(f"Process complete! XML saved to: {output_xml}")

def main():
    # We copied the logic from nain -if __name__ == "__main__":
    path_input = input("Enter the full path to the .shp file: ").strip('"')
    process_shapefile_to_xml(path_input)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run from terminal: python src/raw_shp_to_xml.py "file_path.shp"
        target_file = sys.argv[1]
        process_shapefile_to_xml(target_file)
    else:
        # Eanual run
        path_input = input("Enter the full path to the .shp file: ").strip('"')
        process_shapefile_to_xml(path_input)