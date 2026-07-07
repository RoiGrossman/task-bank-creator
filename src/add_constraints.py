import shutil
import geopandas as gpd
import numpy as np
import datetime
import sys
from pathlib import Path

# Base path setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

DATA_PROCESSED = BASE_DIR / "2-data" / "processed"
OUTPUT_TARGETS = DATA_PROCESSED / "output_targets"

def load_shapefile(shp_path):
    if not shp_path.exists():
        print(f"Error: Target file not found at {shp_path}")
        return None
    print(f"Loading shapefile from {shp_path}...")
    return gpd.read_file(shp_path)

def apply_constraint(gdf, mode, rng):
    # Determine eligible pool for sampling
    eligible_indices = gdf.index.tolist()
    
    # Optional selective filtering based on existing parameters
    if input("Apply constraint selectively? (y/n): ").lower() == 'y':
        print("\nAvailable parameters for filtering:")
        columns = list(gdf.columns)
        for i, col in enumerate(columns):
            print(f"[{i}] {col}")
        
        while True:
            choice = input(f"Select parameter index (0-{len(columns)-1}): ")
            if choice.isdigit() and int(choice) < len(columns):
                col = columns[int(choice)]
                break
            print("Invalid selection.")
            
        val_min = float(input(f"Filter min value for '{col}': "))
        val_max = float(input(f"Filter max value for '{col}': "))
        
        mask = (gdf[col] >= val_min) & (gdf[col] <= val_max)
        eligible_indices = gdf.index[mask].tolist()
        print(f"Objects matching criteria: {len(eligible_indices)}")
    
    # Input count to constrain
    print(f"There are {len(eligible_indices)} objects available.")
    while True:
        count = int(input("Number of objects to constrain: "))
        if 0 < count <= len(eligible_indices):
            break
        print(f"Please enter a number between 1 and {len(eligible_indices)}.")

    # Sampling
    target_indices = rng.choice(eligible_indices, size=count, replace=False)
    
    # Initialize new columns if missing
    new_cols = {
        'urgent_dl': False, 'el_from': np.nan, 'el_to': np.nan, 
        'az_from': np.nan, 'az_to': np.nan, 'hour_range': None, 
        'resolution': np.nan
    }
    for col, default in new_cols.items():
        if col not in gdf.columns:
            gdf[col] = default

    # Apply constraints based on mode
    if mode == '1':
        gdf.loc[target_indices, 'urgent_dl'] = True
    elif mode == '2':
        gdf.loc[target_indices, 'el_from'] = float(input("Enter elevation from... (0-90): "))
        gdf.loc[target_indices, 'el_to'] = float(input("Enter elevation to... (0-90): "))
    elif mode == '3':
        gdf.loc[target_indices, 'az_from'] = float(input("Enter azimuth from... (0-359): "))
        gdf.loc[target_indices, 'az_to'] = float(input("Enter azimuth to... (0-359): "))
    elif mode == '4':
        gdf.loc[target_indices, 'hour_range'] = input("Enter hour range (hh:mm-hh:mm): ")
    elif mode == '5':
        gdf.loc[target_indices, 'resolution'] = float(input("Enter resolution: "))
        
    return gdf

def main():
    shp_path = OUTPUT_TARGETS / 'prioritized_targets.shp'
    gdf = load_shapefile(shp_path)
    if gdf is None: return

    applied_logic = []
    
    while True:
        print("\nAvailable Constraints:\n[1] Urgent\n[2] Elevation\n[3] Azimuth\n[4] Hour Range\n[5] Resolution")
        mode = input("Select mode [1-5]: ").strip()
        
        is_det = input("Mode [1] Random, [2] Deterministic: ").strip() == '2'
        rng = np.random.default_rng(seed=42 if is_det else None)
        
        gdf = apply_constraint(gdf, mode, rng) 
        applied_logic.append(f"c{mode}")
        
        if input("\nAdd another constraint? (y/n): ").lower() != 'y':
            break

    # Export results
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = DATA_PROCESSED / f"shuffled_{'_'.join(applied_logic)}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle sidecar files and save
    if (src_prj := shp_path.with_suffix('.prj')).exists():
        shutil.copy(src_prj, out_dir / 'prioritized_targets.prj')
    
    gdf.to_file(out_dir / 'prioritized_targets.shp')
    print(f"\nSuccess! Saved to: {out_dir}")

if __name__ == "__main__":
    main()