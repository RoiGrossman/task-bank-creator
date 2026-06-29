import sys
import os
import datetime
import shutil
import numpy as np
import geopandas as gpd
from pathlib import Path
from sklearn.cluster import DBSCAN

# הגדרת נתיב השורש
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# ייבוא מה-src
from src.xml_exporter import export_to_xml

# הגדרת נתיבים לפי העץ שלך
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"
OUTPUT_TARGETS = DATA_PROCESSED / "output_targets"

def load_shapefile(shp_path):
    if not shp_path.exists():
        print(f"Error: Target file not found at {shp_path}")
        return None
    print(f"Loading shapefile from {shp_path}...")
    return gpd.read_file(shp_path)

def apply_shuffle_logic(gdf, mode):
    # שמירה על סדר מקורי
    if 'orig_idx' not in gdf.columns:
        gdf['orig_idx'] = gdf.index
        
    existing_priorities = sorted(gdf['Priority'].tolist())
    centroids = gdf.geometry.centroid
    
    mode_names = {
        '1': 'pure_random_permutation',
        '2': 'priority_inversion',
        '3': 'top_priorities_to_extremes',
        '4': 'clustering_top_priorities'
    }
    logic_name = mode_names.get(mode, 'unknown')
    
    if mode == '1':
        gdf['Priority'] = np.random.permutation(gdf['Priority'].values)
        
    elif mode == '2':
        max_p, min_p = max(existing_priorities), min(existing_priorities)
        gdf['Priority'] = max_p + min_p - gdf['Priority']
        
    elif mode == '3':
        # חישוב מרחק מהמרכז כדי לדחוף חשיבות גבוהה לקצוות
        min_x, max_x = centroids.x.min(), centroids.x.max()
        min_y, max_y = centroids.y.min(), centroids.y.max()
        norm_x = (centroids.x - min_x) / (max_x - min_x) if max_x > min_x else 0
        norm_y = (centroids.y - min_y) / (max_y - min_y) if max_y > min_y else 0
        # המרחק מהמרכז (0.5, 0.5)
        distances = np.sqrt((norm_x - 0.5)**2 + (norm_y - 0.5)**2)
        
        # מיון לפי מרחק מהמרכז (הכי רחוק = הכי קרוב לקצה)
        gdf['tmp_dist'] = distances
        gdf = gdf.sort_values(by='tmp_dist', ascending=False).reset_index(drop=True)
        # הקצאת התיעדופים הכי גבוהים לקצוות
        gdf['Priority'] = existing_priorities
        gdf = gdf.drop(columns=['tmp_dist'])
        
    elif mode == '4':
        # חישוב קלאסטרים (DBSCAN)
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
        gdf['Priority'] = new_priorities
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

    # יצירת תיקיית פלט תחת processed
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_output_folder = DATA_PROCESSED / f"shuffled_{logic_name}_{timestamp}"
    target_output_folder.mkdir(parents=True, exist_ok=True)
    
    # העתקת ה-prj
    src_prj = shp_path.with_suffix('.prj')
    if src_prj.exists():
        shutil.copy(src_prj, target_output_folder / 'prioritized_targets.prj')

    # שמירת Shapefile
    new_shp_path = target_output_folder / 'prioritized_targets.shp'
    gdf[['id', 'Priority', 'geometry']].to_file(new_shp_path)
    
    # שמירת XML
    output_xml = target_output_folder / f'tasks_shuffled_{mode}_{timestamp}.xml'
    export_to_xml(gdf, str(output_xml))
    
    print(f"\nSuccess! Saved to: {target_output_folder}")

if __name__ == "__main__":
    main()