import os
import geopandas as gpd
# הגדרת נתיב השורש (התיקייה שבה נמצאת 0 project-root)
# מניח שהסקריפט נמצא בתוך src, אז עולים רמה אחת למעלה
BASE_DIR = Path(__file__).resolve().parent.parent

# הוספת השורש לנתיבי החיפוש של פייתון (כדי שה-imports יעבדו)
sys.path.append(str(BASE_DIR))

# עכשיו אפשר לגשת לכל תיקייה בקלות:
DATA_RAW = BASE_DIR / "2-data" / "raw"
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"
folder = 'output_targets'

if not os.path.exists(folder):
    print(f"Error: Folder '{folder}' does not exist.")
else:
    # Find all .shp files in the output directory
    shp_files = [f for f in os.listdir(folder) if f.endswith('.shp')]
    
    if not shp_files:
        print(f"No .shp files found in '{folder}'. Available files: {os.listdir(folder)}")
    else:
        print(f"Found {len(shp_files)} Shapefile layer(s) to check:\n")
        
        for shp_file in shp_files:
            path = os.path.join(folder, shp_file)
            print(f"========================================")
            print(f"Checking Layer: {shp_file}")
            print(f"========================================")
            
            try:
                gdf = gpd.read_file(path)
                print(f"Total features (polygons): {len(gdf)}")
                print(f"Coordinate Reference System (CRS): {gdf.crs}\n")
                
                print("Available Columns:")
                print(list(gdf.columns), "\n")
                
                print("Sample Data (First 3 Rows):")
                print(gdf.head(3))
                print("\n")
                
            except Exception as e:
                print(f"Error reading {shp_file}: {e}\n")