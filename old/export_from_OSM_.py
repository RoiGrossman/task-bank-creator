import os
import osmnx as ox
from datetime import datetime
# הגדרת נתיב השורש (התיקייה שבה נמצאת 0 project-root)
# מניח שהסקריפט נמצא בתוך src, אז עולים רמה אחת למעלה
BASE_DIR = Path(__file__).resolve().parent.parent

# הוספת השורש לנתיבי החיפוש של פייתון (כדי שה-imports יעבדו)
sys.path.append(str(BASE_DIR))

# עכשיו אפשר לגשת לכל תיקייה בקלות:
DATA_RAW = BASE_DIR / "2-data" / "raw"
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"

def extract_osm_layer():
    # 1. קלט מהמשתמש
    pbf_path = input("Enter the filename of your .pbf file (e.g., israel.pbf): ")
    
    # בדיקה אם הקובץ באמת קיים בתיקייה הנוכחית
    if not os.path.isfile(pbf_path):
        print(f"Error: The file '{pbf_path}' was not found in the current directory.")
        return # עוצר את הריצה אם הקובץ לא נמצא
        
    country_name = input("Enter country name: ").lower()
    key = input("Enter OSM key: ")
    val = input("Enter OSM value: ")
    
    # --- תוספת: הגדרת תיקיית עבודה מקומית למניעת שגיאות הרשאות ---
    working_dir = os.getcwd()
    temp_dir = os.path.join(working_dir, "temp_osm")
    os.makedirs(temp_dir, exist_ok=True)
    # נגדיר ל-osmnx להשתמש בתיקייה הזו אם הוא צריך
    ox.settings.cache_folder = temp_dir
    # -----------------------------------------------------------
    
    # 2. הכנת התיקייה והשם הייחודי
    os.makedirs("extracted_data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"extracted_data/{country_name}_{key}_{val}_{timestamp}.geojson"
    
    print(f"Extracting {key}={val} from {pbf_path}...")
    
    try:
        tags = {key: val}
        # שימוש בנתיב המקומי (וודא שהקובץ נמצא בתיקיית הפרויקט)
        gdf = ox.features_from_xml(pbf_path, tags=tags)
        
        if not gdf.empty:
            # המרת עמודות מורכבות למחרוזות כדי למנוע שגיאות GeoJSON
            gdf = gdf.astype(str)
            gdf.to_file(filename, driver="GeoJSON")
            print(f"Success! Saved to {filename}")
        else:
            print("No features found for this filter.")
            
    except Exception as e:
        print(f"Error during extraction: {e}")

if __name__ == "__main__":
    extract_osm_layer()