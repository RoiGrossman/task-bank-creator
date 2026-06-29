import os
import datetime
import shutil
import numpy as np
import geopandas as gpd
from sklearn.cluster import DBSCAN
from xml_exporter import export_to_xml

# הגדרת נתיב השורש (התיקייה שבה נמצאת 0 project-root)
# מניח שהסקריפט נמצא בתוך src, אז עולים רמה אחת למעלה
BASE_DIR = Path(__file__).resolve().parent.parent

# הוספת השורש לנתיבי החיפוש של פייתון (כדי שה-imports יעבדו)
sys.path.append(str(BASE_DIR))

# עכשיו אפשר לגשת לכל תיקייה בקלות:
DATA_RAW = BASE_DIR / "2-data" / "raw"
DATA_PROCESSED = BASE_DIR / "2-data" / "processed"

def load_shapefile(shp_path):
    if not os.path.exists(shp_path):
        print(f"Error: Target file not found at {shp_path}")
        return None
    print(f"Loading shapefile from {shp_path}...")
    return gpd.read_file(shp_path)

def apply_shuffle_logic(gdf, mode):
    existing_priorities = sorted(gdf['Priority'].tolist())
    total_features = len(gdf)
    centroids = gdf.geometry.centroid
    
    mode_names = {
        '1': 'pure_random_permutation',
        '2': 'priority_inversion',
        '3': 'top_priorities_to_extremes',
        '4': 'clustering_top_priorities'
    }
    folder_name = mode_names[mode]
    print(f"Applying shuffle logic: {folder_name}")
    
    if mode == '1':
        gdf['Priority'] = np.random.permutation(gdf['Priority'].values)
        
    elif mode == '2':
        max_p, min_p = max(existing_priorities), min(existing_priorities)
        gdf['Priority'] = max_p + min_p - gdf['Priority']
        
    elif mode == '3':
        min_x, max_x = centroids.x.min(), centroids.x.max()
        min_y, max_y = centroids.y.min(), centroids.y.max()
        norm_x = (centroids.x - min_x) / (max_x - min_x) if max_x > min_x else 0
        norm_y = (centroids.y - min_y) / (max_y - min_y) if max_y > min_y else 0
        distances = np.sqrt((norm_x - norm_x.mean())**2 + (norm_y - norm_y.mean())**2)
        gdf['tmp_dist'] = distances
        gdf = gdf.sort_values(by='tmp_dist', ascending=False).reset_index(drop=True)
        gdf['Priority'] = existing_priorities
        gdf = gdf.drop(columns=['tmp_dist'])
        
    elif mode == '4':
        from sklearn.cluster import DBSCAN
        
        # 1. חישוב קלאסטרים
        coords = np.column_stack((centroids.x.values, centroids.y.values))
        bbox_diagonal = np.sqrt(np.sum((coords.max(axis=0) - coords.min(axis=0))**2))
        eps_value = max(bbox_diagonal * 0.05, 0.00001)
        db = DBSCAN(eps=eps_value, min_samples=3).fit(coords)
        gdf['cluster_id'] = db.labels_
        
        # 2. הכנת "קופת" התיעדופים המקוריים
        available_priorities = sorted(existing_priorities)
        
        # 3. זיהוי ומיון קלאסטרים לפי גודל (מהגדול לקטן)
        # מסננים את הרעש (-1) כדי שהם לא יקבלו את התיעדופים הטובים
        cluster_counts = gdf[gdf['cluster_id'] != -1]['cluster_id'].value_counts()
        sorted_cluster_ids = cluster_counts.index.tolist()
        
        # 4. הקצאת תיעדופים
        new_priorities = np.zeros(len(gdf), dtype=int)
        mask_assigned = np.zeros(len(gdf), dtype=bool)
        
        # הקצאה לקלאסטרים
        for cid in sorted_cluster_ids:
            indices = gdf[gdf['cluster_id'] == cid].index
            count = len(indices)
            # לוקחים מהקופה את הכמות הדרושה (מהנמוך לגבוה)
            p_slice = available_priorities[:count]
            new_priorities[indices] = p_slice
            mask_assigned[indices] = True
            # מסירים מהקופה
            available_priorities = available_priorities[count:]
            
        # 5. השלמת השאריות (בודדים ורעש) עם מה שנשאר בקופה
        remaining_indices = gdf[~mask_assigned].index
        new_priorities[remaining_indices] = available_priorities
        
        gdf['Priority'] = new_priorities
        gdf = gdf.drop(columns=['cluster_id'])

    # החזרת הסדר הפיזי המקורי (קריטי!)
    if 'orig_idx' in gdf.columns:
        gdf = gdf.sort_values(by='orig_idx').reset_index(drop=True)
        gdf = gdf.drop(columns=['orig_idx'])

    return gdf, folder_name

def main():
    input_folder = 'output_targets'
    shp_filename = 'prioritized_targets.shp'
    shp_path = os.path.abspath(os.path.join(input_folder, shp_filename))
    
    # 1. טעינת הנתונים המקוריים (נשארים תמיד שלמים בחוץ)
    gdf = load_shapefile(shp_path)
    if gdf is None:
        return
        
    # 2. תפריט בחירה למשתמש
    print("\nAvailable Shuffling Options:")
    print("[1] Pure Random Permutation")
    print("[2] Priority Inversion (High <-> Low)")
    print("[3] Push Top Priorities [1,2,3...] to Extremes (Peripheral)")
    print("[4] Cluster Top Priorities [1,2,3...] Together in Dense Areas")
    
    mode = input("\nSelect shuffling mode [1-4]: ").strip()
    if mode not in ['1', '2', '3', '4']:
        print("Invalid mode selected. Exiting.")
        return

    # 3. הרצת לוגיקת הערבוב וקבלת שם הלוגיקה
    gdf, logic_name = apply_shuffle_logic(gdf, mode)

    # 4. יצירת תיקיית יעד ייעודית (כולל שם הפונקציה וחותמת זמן)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_output_folder = os.path.join(input_folder, f"shuffled_{logic_name}_{timestamp}")
    os.makedirs(target_output_folder, exist_ok=True)
    
    # העתקת קובץ ה-Projection (.prj) המקורי כדי שהשכבה החדשה תשמור על מערכת הקואורדינטות
    src_prj = os.path.splitext(shp_path)[0] + '.prj'
    if os.path.exists(src_prj):
        shutil.copy(src_prj, os.path.join(target_output_folder, 'prioritized_targets.prj'))

    # 5. שמירת קבצי ה-Shapefile החדשים בתוך תת-התיקייה החדשה
    new_shp_path = os.path.join(target_output_folder, 'prioritized_targets.shp')
    try:
        # כאן אנחנו משמיטים את orig_idx כדי שהקובץ הסופי יכיל רק id ו-Priority
        keep_columns = ['id', 'Priority', 'geometry']
        gdf_to_save = gdf[keep_columns]
        
        gdf_to_save.to_file(new_shp_path)
        print(f"\nSuccess! Original file left untouched.")
        print(f"New shuffled dataset saved with UIDs to: {new_shp_path}")
    except Exception as e:
        print(f"Error saving updated shapefile: {e}")

    # שמירת ה-XML בתוך תיקיית הפלט הייעודית שנפתחה (target_output_folder)
    output_xml = os.path.join(target_output_folder, f'tasks_shuffled_{mode}_{timestamp}.xml')
    export_to_xml(gdf, output_xml)

    
if __name__ == "__main__":
    main()