import sys
from pathlib import Path
import datetime
import subprocess
import numpy as np
import geopandas as gpd
import uuid
import json
import os

# Define base dir
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "src"))

# Import from local package
from xml_exporter import export_to_xml

# Dynamic paths
DATA_RAW = BASE_DIR / "2-data" / "raw"
DATA_EXPORT = BASE_DIR / "1-raw_OSM_exports"
OUTPUT_DIR = BASE_DIR / "2-data" / "processed" / "output_targets"
BOUNDARY_PATH = BASE_DIR / "2-data" / "raw" / "AOI.kml"

# Final Values
SCAN_AZIMUTH_MIN = 0.0
SCAN_AZIMUTH_MAX = 359.999
LENGTH_BEFORE_CENTER = 6.0
LENGTH_AFTER_CENTER = 6.0


def load_and_filter_geometry(input_path, log_lines):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines.append(f"[{timestamp}] Loading raw data from '{input_path}'...")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    gdf = gpd.GeoDataFrame.from_features(data['features'])
    gdf['geometry'] = gdf.make_valid()
    
    initial_count = len(gdf)
    log_lines.append(f"-> Total raw rows loaded: {initial_count}")
    
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    gdf = gdf[gdf.geometry.type == 'Polygon'].reset_index(drop=True)
    gdf = gdf[~gdf.is_empty].reset_index(drop=True)
    
    exploded_count = len(gdf)
    log_lines.append(f"-> Features after exploding and filtering for Polygons only: {exploded_count}")
    
    wkt_series = gdf.geometry.to_wkt()
    duplicate_mask = wkt_series.duplicated(keep='first')
    duplicate_count = duplicate_mask.sum()
    
    if duplicate_count > 0:
        gdf = gdf[~duplicate_mask].reset_index(drop=True)
        log_lines.append(f"-> [WARNING] Found and removed {duplicate_count} exact duplicate geometries.")
    else:
        log_lines.append("-> No duplicate geometries detected.")
        
    return gdf

def apply_spatial_boundary(gdf, boundary_file, log_lines):
    boundary_gdf = gpd.read_file(boundary_file)
    boundary_gdf['geometry'] = boundary_gdf.make_valid()
    gdf['geometry'] = gdf.make_valid()
    
    if boundary_gdf.crs is None: boundary_gdf = boundary_gdf.set_crs("EPSG:4326")
    if gdf.crs is None: gdf = gdf.set_crs("EPSG:4326")
    if gdf.crs != boundary_gdf.crs: boundary_gdf = boundary_gdf.to_crs(gdf.crs)
        
    return gpd.clip(gdf, boundary_gdf)

def apply_priority_by_mode(gdf, mode, min_p, max_p, log_lines, is_deterministic):
    if len(gdf) == 0: return gdf
    n = len(gdf)
    rng = np.random.default_rng(seed=42) if is_deterministic else np.random.default_rng()
    
    if mode == '1':
        raw = rng.normal(loc=0.0, scale=1.0, size=n)
        norm = (raw - raw.min()) / (raw.max() - raw.min()) if raw.max() > raw.min() else np.zeros(n)
        priorities = min_p + (norm * (max_p - min_p))
    elif mode == '2':
        priorities = rng.integers(min_p, max_p + 1, size=n)
    elif mode == '3':
        choices = np.arange(min_p, max_p + 1)
        weights = np.linspace(1, 5, len(choices))
        priorities = rng.choice(choices, size=n, p=weights/weights.sum())
    else:
        priorities = np.full(n, min_p)
        
    gdf['priority'] = np.round(priorities).astype(int)
    return gdf

def save_execution_summary_to_file(gdf, shp_path, summary_path, log_lines, sample_rows_to_show):
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("PROCESS EXECUTION LOG\n" + "="*60 + "\n")
        for line in log_lines: f.write(line + "\n")
        f.write("\nDATASET SUMMARY\n" + "="*60 + "\n")
        f.write(f"Output: {shp_path}\nTotal features: {len(gdf)}\n\n")
        f.write(f"Sample Data:\n{gdf.head(sample_rows_to_show)}\n")

def main():
    log_lines = [f"Execution started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    
    # Define input file
    input_file = BASE_DIR / "2-data" / "raw" / "export.geojson"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        min_p = int(input("Min priority: "))
        max_p = int(input("Max priority: "))
        limit_input = input("Max features (Enter for all): ")
        max_features = int(limit_input) if limit_input.strip().isdigit() else None
        sampling_mode = input("Mode - [1] Random, [2] Deterministic: ").strip()
        is_deterministic = (sampling_mode == '2')
        dist_mode = input("Priority distribution [1] Normal distribution, [2] Uniform, [3] Linear ascending: ").strip()
        sample_rows_to_show = int(input("Rows to display in summary: ") or 3)
    except ValueError:
        print("Invalid input.")
        return

    gdf = load_and_filter_geometry(str(input_file), log_lines)
    gdf = apply_spatial_boundary(gdf, str(BOUNDARY_PATH), log_lines)
    
    if len(gdf) == 0:
        print("\n[ERROR] No features found. Check input/AOI.")
        return
        
    if max_features and max_features < len(gdf):
        if is_deterministic:
            gdf['centroid_x'] = gdf.geometry.centroid.x
            gdf = gdf.sort_values(by='centroid_x').iloc[np.linspace(0, len(gdf)-1, max_features, dtype=int)].reset_index(drop=True)
            gdf = gdf.drop(columns=['centroid_x'])
        else:
            gdf = gdf.sample(n=max_features).reset_index(drop=True)
    
    gdf = apply_priority_by_mode(gdf, dist_mode, min_p, max_p, log_lines, is_deterministic)
    gdf['id'] = [str(uuid.uuid4()) for _ in range(len(gdf))]
    gdf['scanAzMin'] = SCAN_AZIMUTH_MIN # This field is implemented in non-Strategy .xml only!
    gdf['scanAzMax'] = SCAN_AZIMUTH_MAX # This field is implemented in non-Strategy .xml only!
    gdf['LenBefCntr'] = LENGTH_BEFORE_CENTER # This field is implemented in non-Strategy .xml only!
    gdf['LenAftCntr'] = LENGTH_AFTER_CENTER # This field is implemented in non-Strategy .xml only!
    gdf = gdf[['id', 'priority', 'geometry', 'scanAzMin', 'scanAzMax', 'LenBefCntr', 'LenAftCntr']]
    
    output_shp = OUTPUT_DIR / 'prioritized_targets.shp'
    gdf.to_file(str(output_shp))
    
    summary_path = OUTPUT_DIR / 'summary.txt'
    save_execution_summary_to_file(gdf, str(output_shp), str(summary_path), log_lines, sample_rows_to_show)
    
    not_strategy_data = os.environ.get('STRATEGY_XML', 'false') == 'true'
    export_to_xml(gdf, str(OUTPUT_DIR / 'prioritized_targets.xml'), not_strategy_data=not_strategy_data)

    print(f"Columns in GDF: {gdf.columns.tolist()}")
    
    if 'priority' in gdf.columns:
        priority_counts = gdf['priority'].value_counts().sort_index()
        summary_path = OUTPUT_DIR / 'summary.txt'
        
        print(f"Attempting to write summary to: {summary_path}")
        
        with open(summary_path, 'a', encoding='utf-8') as f:
            f.write("\n\n--- Priority Distribution ---\n")
            for priority, count in priority_counts.items():
                f.write(f"Priority {priority}: {count} targets\n")
        
        print("Summary write complete.")
    else:
        print("ERROR: Column 'Priority' not found in data. Available columns:", gdf.columns.tolist())

    # Open file
    subprocess.Popen(['notepad.exe', str(summary_path)])

if __name__ == "__main__":
    main()