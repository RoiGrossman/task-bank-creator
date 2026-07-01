import sys
import os
import datetime
import shutil
import numpy as np
import geopandas as gpd
from pathlib import Path
from sklearn.cluster import DBSCAN

# Define base directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import from source
from src.xml_exporter import export_to_xml

# Define routes
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"
OUTPUT_TARGETS = DATA_PROCESSED / "output_targets"

def load_shapefile(shp_path):
    if not shp_path.exists():
        print(f"Error: Target file not found at {shp_path}")
        return None
    print(f"Loading shapefile from {shp_path}...")
    return gpd.read_file(shp_path)

def apply_shuffle_logic(gdf, mode):
    if 'orig_idx' not in gdf.columns:
        gdf['orig_idx'] = gdf.index
        
    existing_priorities = sorted(gdf['priority'].tolist())
    centroids = gdf.geometry.centroid
    
    mode_names = {
        '1': 'pure_random_permutation',
        '2': 'priority_inversion',
        '3': 'top_priorities_to_extremes',
        '4': 'clustering_top_priorities'
    }
    logic_name = mode_names.get(mode, 'unknown')
    
    if mode == '1':
        gdf['priority'] = np.random.permutation(gdf['priority'].values)
        
    elif mode == '2':
        max_p, min_p = max(existing_priorities), min(existing_priorities)
        gdf['priority'] = max_p + min_p - gdf['priority']
        
    elif mode == '3':
        # Calculate distance from center to apply high importance to edges
        min_x, max_x = centroids.x.min(), centroids.x.max()
        min_y, max_y = centroids.y.min(), centroids.y.max()
        norm_x = (centroids.x - min_x) / (max_x - min_x) if max_x > min_x else 0
        norm_y = (centroids.y - min_y) / (max_y - min_y) if max_y > min_y else 0
        # Distance from center (0.5, 0.5)
        distances = np.sqrt((norm_x - 0.5)**2 + (norm_y - 0.5)**2)
        
        # Sort by distance
        gdf['tmp_dist'] = distances
        gdf = gdf.sort_values(by='tmp_dist', ascending=False).reset_index(drop=True)
        # Apply priorities
        gdf['priority'] = existing_priorities
        gdf = gdf.drop(columns=['tmp_dist'])
        
    elif mode == '4':
        # Calculate clusters (DBSCAN)
        coords = np.column_stack((centroids.x.values, centroids.y.values))
        bbox_diagonal = np.sqrt(np.sum((coords.max(axis=0) - coords.min(axis=0))**2))
        eps_value = max(bbox_diagonal * 0.05, 0.00001)
        db = DBSCAN(eps=eps_value, min_samples=3).fit(coords)
        gdf['cluster_id'] = db.labels_
        
        available_priorities = sorted(existing_priorities)
        cluster_counts = gdf[gdf['cluster_id'] != -1]['cluster_id'].value_counts()
        sorted_cluster_ids = cluster_counts.index.tolist()
        
        new_priorities = np.zeros(len(gdf), dtype=int)
        mask_assigned = np.zeros(len(gdf), dtype=bool)
        
        for cid in sorted_cluster_ids:
            indices = gdf[gdf['cluster_id'] == cid].index
            count = len(indices)
            p_slice = available_priorities[:count]
            new_priorities[indices] = p_slice
            mask_assigned[indices] = True
            available_priorities = available_priorities[count:]
            
        remaining_indices = gdf[~mask_assigned].index
        new_priorities[remaining_indices] = available_priorities
        gdf['priority'] = new_priorities
        gdf = gdf.drop(columns=['cluster_id'])

    return gdf, logic_name

def main():
    shp_path = OUTPUT_TARGETS / 'prioritized_targets.shp'
    
    gdf = load_shapefile(shp_path)
    if gdf is None: return
        
    print("\nAvailable Shuffling Options:")
    print("[1] Pure Random Permutation\n[2] Priority Inversion\n[3] Push Top Priorities to Periphery\n[4] Cluster Top Priorities")
    
    mode = input("\nSelect shuffling mode [1-4]: ").strip()
    if mode not in ['1', '2', '3', '4']:
        print("Invalid mode selected.")
        return

    gdf, logic_name = apply_shuffle_logic(gdf, mode)

    # Create output folder under processed
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_output_folder = DATA_PROCESSED / f"shuffled_{logic_name}_{timestamp}"
    target_output_folder.mkdir(parents=True, exist_ok=True)
    
    # Copy prj
    src_prj = shp_path.with_suffix('.prj')
    if src_prj.exists():
        shutil.copy(src_prj, target_output_folder / 'prioritized_targets.prj')

    # Save Shapefile
    new_shp_path = target_output_folder / 'prioritized_targets.shp'
    gdf[['id', 'priority', 'geometry']].to_file(new_shp_path)
    
    # Save XML
    output_xml = target_output_folder / f'tasks_shuffled_{mode}_{timestamp}.xml'
    export_to_xml(gdf, str(output_xml))
    
    print(f"\nSuccess! Saved to: {target_output_folder}")

if __name__ == "__main__":
    main()