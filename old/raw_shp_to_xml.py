import geopandas as gpd
import os
import sys
# וודא שהקובץ xml_exporter.py נמצא באותה תיקייה
from src.xml_exporter import export_to_xml 

# הגדרת נתיב השורש (התיקייה שבה נמצאת 0 project-root)
# מניח שהסקריפט נמצא בתוך src, אז עולים רמה אחת למעלה
BASE_DIR = Path(__file__).resolve().parent.parent

# הוספת השורש לנתיבי החיפוש של פייתון (כדי שה-imports יעבדו)
sys.path.append(str(BASE_DIR))

# עכשיו אפשר לגשת לכל תיקייה בקלות:
DATA_RAW = BASE_DIR / "2-data" / "raw"
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"


def process_shapefile_to_xml(shp_path):
    if not os.path.exists(shp_path):
        print(f"Error: File not found at {shp_path}")
        return

    print(f"Loading shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path)
    
    # בדיקת נתונים
    print(f"DEBUG: Features found: {len(gdf)}")
    print(f"DEBUG: Available columns: {list(gdf.columns)}")
    
    if len(gdf) == 0:
        print("CRITICAL: File is empty. No XML created.")
        return
        
    # בדיקת עמודות חובה
    required = ['id', 'Priority']
    missing = [col for col in required if col not in gdf.columns]
    if missing:
        print(f"CRITICAL: Missing columns in file: {missing}")
        return

    output_xml = os.path.splitext(shp_path)[0] + ".xml"
    
    # הפעלה
    export_to_xml(gdf, output_xml)
    print(f"Process complete! XML saved to: {output_xml}")

if __name__ == "__main__":
    # מאפשר לך להריץ מהטרמינל: python raw_shp_to_xml.py "my_file.shp"
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        process_shapefile_to_xml(target_file)
    else:
        # או פשוט להדביק כאן את הנתיב ידנית לריצה מהירה
        path = input("Enter the full path to the .shp file: ").strip('"')
        process_shapefile_to_xml(path)