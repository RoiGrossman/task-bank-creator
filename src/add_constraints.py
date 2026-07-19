import shutil
import geopandas as gpd
import numpy as np
import datetime
import sys
from pathlib import Path
import os

# Base path setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import from local package
from xml_exporter import export_to_xml

DATA_PROCESSED = BASE_DIR / "2-data" / "processed"
OUTPUT_TARGETS = DATA_PROCESSED / "output_targets"

# For setting a random value per constraint, this deictionary defines possible values
PARAM_CONFIG = {
    'el': {'min': 0, 'max': 90, 'step': 1},
    'az': {'min': 0, 'max': 359.999999, 'step': 10},
    'resolution': {'min': 0.8, 'max': 1.5, 'step': 0.1}, # 0.8 As min resolution for Etgar B
    'scanAz': {'min': 0, 'max': 359.999999, 'step': 10},
    'Len': {'min': 1000, 'max': 200000, 'step': 1000}
}

MODE_MAP = {
    '2': {'cols': ['minElev', 'maxElev'], 'param': 'el'},
    '3': {'cols': ['minViewAz', 'maxViewAz'], 'param': 'az'},
    '6': {'cols': ['resolution'], 'param': 'resolution'},
    '7': {'cols': ['scanAzMin', 'scanAzMax'], 'param': 'scanAz'},
    '8': {'cols': ['LenBefCntr', 'LenAftCntr'], 'param': 'Len'}
}

OFFSET_CONFIG = {
    'el': {'base':20, 'variance':0},       
    'az': {'base':60, 'variance':0},       
    'scanAz': {'base':0, 'variance':0},
    'Len': {'base':0, 'variance':0}    
}

def load_shapefile(shp_path):
    if not shp_path.exists():
        print(f"Error: Target file not found at {shp_path}")
        return None
    print(f"Loading shapefile from {shp_path}...")
    return gpd.read_file(shp_path)

def get_random_value(param_key, rng):
    conf = PARAM_CONFIG[param_key]
    num_steps = int((conf['max'] - conf['min']) / conf['step'])
    random_step = rng.integers(0, num_steps + 1)
    return conf['min'] + (random_step * conf['step'])

def apply_constraint(gdf, mode, rng):
    # Determine eligible pool for sampling
    eligible_indices = gdf.index.tolist()
    
    # Optional selective filtering based on existing parameters
    if input("Apply constraint based on another constraint? (y/n): ").lower() == 'y':
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

    # Apply constraints based on mode
    if mode in MODE_MAP:
        config = MODE_MAP[mode]
        cols = config['cols']
        param_key = config['param']
        
        choice_type = input("Enter values [M]anually or [R]andomly? ").upper()
        
        if choice_type == 'R':
            for idx in target_indices:
                val_min = round(get_random_value(param_key, rng), 1)
                config_offset = OFFSET_CONFIG.get(param_key, {'base': 0, 'variance': 0})
                base_val = config_offset.get('base', 0)
                var_val = config_offset.get('variance', 0)
                
                dynamic_offset = base_val + rng.integers(-var_val, var_val + 1)
                val_max = val_min + dynamic_offset
            
                if val_max > PARAM_CONFIG[param_key]['max']:
                    val_max = PARAM_CONFIG[param_key]['max']

                if len(cols) == 2:
                    gdf.loc[idx, cols] = [val_min, val_max]
                else:
                    gdf.loc[idx, cols] = val_min
            print(f"Random values assigned uniquely.")
        else:
            for col in cols:
                val = float(input(f"Enter value for '{col}': "))
                gdf.loc[target_indices, col] = val
            print(f"Manual values assigned.")

    elif mode == '1':
        gdf.loc[target_indices, 'urgent_dl'] = True
    elif mode == '4':
        start_date = input("Enter start date (YYYY-MM-DDTHH:MM:SS.000): ")
        end_date = input("Enter end date (YYYY-MM-DDTHH:MM:SS.000): ")
        gdf.loc[target_indices, 'date_start'] = start_date
        gdf.loc[target_indices, 'date_end'] = end_date
    elif mode == '5':
        gdf.loc[target_indices, 'hour_range'] = input("Enter hour range (hh:mm-hh:mm): ")
    
    return gdf


def main():
    shp_path = OUTPUT_TARGETS / 'prioritized_targets.shp'
    gdf = load_shapefile(shp_path)
    if gdf is None: return

    applied_logic = []

    # Initialize new columns if missing
    new_cols = {
        'urgent_dl': False, 'minElev': np.nan, 'maxElev': np.nan, 
        'minViewAz': np.nan, 'maxViewAz': np.nan, 'date_start': None, 'date_end': None,
        'hour_range': None, 'resolution': np.nan, 'scanAzMin': np.nan, 'scanAzMax': np.nan, 
        'LenBefCntr': np.nan, 'LenAftCntr': np.nan
    }
    for col, default in new_cols.items():
        if col not in gdf.columns:
            gdf[col] = default
            if col in ['scanAzMin', 'scanAzMax', 'LenBefCntr', 'LenAftCntr', 'minElev', 'maxElev', 'minViewAz', 'maxViewAz', 'resolution']:
                gdf[col] = gdf[col].astype(float)
    
    while True:
        print("\nAvailable Constraints:\n[1] Urgent\n[2] Elevation\n[3] Azimuth\n[4] Relevance Date\n[5] Hour Range\n[6] Resolution\n[7] Scan Azimuth\n[8] Scan Length")
        mode = input("Select mode [1-8]: ").strip()
        
        is_det = input("Mode [1] Random, [2] Deterministic: ").strip() == '2'
        rng = np.random.default_rng(seed=42 if is_det else None)
        
        gdf = apply_constraint(gdf, mode, rng) 
        applied_logic.append(f"c{mode}")
        
        if input("\nAdd another constraint? (y/n): ").lower() != 'y':
            break
    
    # Delete Every Column that holds no value at all 
    cols_to_check = ['urgent_dl', 'minElev', 'maxElev', 'minViewAz', 'maxViewAz', 'date_start', 
                 'date_end', 'hour_range', 'resolution', 
                 'scanAzMin', 'scanAzMax', 'LenBefCntr', 'LenAftCntr']

    for col in cols_to_check:
        if col in gdf.columns and gdf[col].isna().all():
            gdf = gdf.drop(columns=[col])
    
    # Export results
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = DATA_PROCESSED / f"shuffled_{'_'.join(applied_logic)}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle sidecar files and save
    if (src_prj := shp_path.with_suffix('.prj')).exists():
        shutil.copy(src_prj, out_dir / 'prioritized_targets.prj')
    
    gdf.to_file(out_dir / 'prioritized_targets.shp')
    print(f"\nSuccess! .shp Saved to: {out_dir}")

    not_strategy_data = os.environ.get('STRATEGY_XML', 'false') == 'true'
    export_to_xml(gdf, str(out_dir / 'prioritized_targets.xml'), not_strategy_data=not_strategy_data)
    print(f"\nSuccess! .xml Saved to: {out_dir}")

if __name__ == "__main__":
    main()