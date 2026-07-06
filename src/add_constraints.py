import sys
import datetime
import shutil
import geopandas as gpd
import numpy as np
import random
from pathlib import Path


# Define base directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Define routes
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"
OUTPUT_TARGETS = DATA_PROCESSED / "output_targets"

def load_shapefile(shp_path):
    if not shp_path.exists():
        print(f"Error: Target file not found at {shp_path}")
        return None
    print(f"Loading shapefile from {shp_path}...")
    return gpd.read_file(shp_path)


def add_constraints(gdf):
    # 1. בחירת סוג האילוץ
    print("\n--- Select Constraint ---")
    print("[1] Urgent Download\n[2] Elevation Angle\n[3] View Azimuth\n[4] Hour Range In Day\n[5] Resolution")
    mode = input("Choice: ").strip()
    
    # מיפוי שמות לוגיים לשם התיקייה
    logic_names = {'1': 'urgent_dl', '2': 'elev_angle', '3': 'view_az', '4': 'hour_range', '5': 'res'}
    logic_name = logic_names.get(mode, 'unknown')
    
    # 2. בחירת מצב
    print("\n--- Select Mode ---")
    print("[1] Random\n[2] Deterministic")
    sampling_mode = input("Choice: ").strip()
    is_deterministic = (sampling_mode == '2')
    
    # 3. בחירת כמות
    count_input = input("Number of objects (default 10): ").strip()
    count = int(count_input) if count_input else 10
    
    # אתחול הגנרטור
    rng = np.random.default_rng(seed=42) if is_deterministic else np.random.default_rng()
    
    # בחירת אובייקטים
    n = len(gdf)
    target_indices = rng.choice(n, size=min(count, n), replace=False)
    
    # עדכון הנתונים ב-GeoDataFrame (עכשיו זה יתבצע!)
    for idx in target_indices:
        if mode == '1': 
            gdf.loc[idx, 'urgent_dl'] = 1
        elif mode == '2':
            val = input(f"Enter min elevation for target {idx}: ")
            gdf.loc[idx, 'el_min'] = val
        elif mode == '3':
            gdf.loc[idx, 'az_min'] = 0
            gdf.loc[idx, 'az_max'] = 360
        # הוסף כאן את שאר המקרים...

    # ה-return מגיע בסוף, אחרי שהלולאה סיימה לעדכן את ה-gdf
    return gdf, logic_name

def main():
    shp_path = OUTPUT_TARGETS / 'prioritized_targets.shp'
    gdf = load_shapefile(shp_path)
    if gdf is None: return

    # נשמור רשימה של שמות האילוצים כדי לבנות את שם התיקייה בסוף
    applied_logic = []

    while True:
        print("\nAvailable Constraints:")
        print("[1] Urgent Download\n[2] Elevation Angle\n[3] View Azimuth\n[4] Hour Range In Day\n[5] Resolution")
        
        mode = input("\nSelect Constraint mode [1-5] (or 'q' to finish): ").strip()
        if mode.lower() == 'q':
            break
            
        if mode not in ['1', '2', '3', '4', '5']:
            print("Invalid mode.")
            continue

        # קריאה לפונקציה שמעדכנת את ה-gdf הקיים
        gdf, logic_name = add_constraints(gdf, mode)
        applied_logic.append(logic_name)
        print(f"Constraint '{logic_name}' added successfully.")

    # ייצוא קבצים רק כאן, אחרי שהלולאה הסתיימה
    save_final_files(gdf, applied_logic)

def save_final_files(gdf, applied_logic):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logic_str = "_".join(applied_logic)
    target_output_folder = DATA_PROCESSED / f"shuffled_{logic_str}_{timestamp}"
    target_output_folder.mkdir(parents=True, exist_ok=True)
    
    new_shp_path = target_output_folder / 'constrained_targets.shp'
    gdf.to_file(new_shp_path)
    print(f"\nSuccess! Saved to: {target_output_folder}")

if __name__ == "__main__":
    main()