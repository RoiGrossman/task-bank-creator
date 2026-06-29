import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# הגדרת נתיב השורש (התיקייה שמעל src)
BASE_DIR = Path(__file__).resolve().parent.parent
# מוודאים ש-BASE_DIR נמצא בנתיב החיפוש
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

def export_to_xml(gdf, output_xml_path):
    """
    מייצא GeoDataFrame לקובץ XML לפי הסכימה הנדרשת.
    output_xml_path יכול להיות נתיב יחסי ל-BASE_DIR או נתיב מלא.
    """
    # יצירת נתיב מוחלט לשמירה
    target_path = Path(output_xml_path)
    if not target_path.is_absolute():
        target_path = BASE_DIR / output_xml_path
    
    # וידוא שהתיקייה קיימת
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # יצירת ה-XML
    root = ET.Element("message", {
        "xmlns": "http://scc/xml/schemas",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })
    
    # 1. Header
    icc_header = ET.SubElement(root, "iccHeader")
    ET.SubElement(icc_header, "messageType").text = "MissionRequirements"
    
    now = datetime.now()
    ET.SubElement(icc_header, "creationTime").text = str(int(now.timestamp()))
    ET.SubElement(icc_header, "creationTimeString").text = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    
    # 2. Data
    mission_data = ET.SubElement(root, "missionRequirementsData")
    ET.SubElement(mission_data, "satellite").text = "OF7"
    ET.SubElement(mission_data, "scowId").text = "Foo#10225#BAR#-#1"
    
    req_list = ET.SubElement(mission_data, "requirementList")
    
    # 3. Geometry processing
    for _, row in gdf.iterrows():
        req = ET.SubElement(req_list, "requirement")
        ET.SubElement(req, "palRequirementId").text = str(row.get('id', 'N/A'))
        ET.SubElement(req, "priority").text = str(row.get('Priority', '0'))
        
        target_data = ET.SubElement(req, "targetImageData")
        poly_boundary = ET.SubElement(target_data, "polygonBoundary")
        
        # טיפול בגיאומטריה
        if row.geometry and row.geometry.geom_type == 'Polygon':
            coords = list(row.geometry.exterior.coords)
            for coord in coords:
                # לוקחים רק את שני האיברים הראשונים (x, y), מתעלמים מ-z אם קיים
                lon, lat = coord[0], coord[1] 
                
                pt = ET.SubElement(poly_boundary, "geographicPoint")
                ET.SubElement(pt, "long").text = f"{lon:.6f}"
                ET.SubElement(pt, "lat").text = f"{lat:.6f}"
                ET.SubElement(pt, "heightUnknown")
    
    # 4. שמירה עם הזחה (indentation) תקינה
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(target_path, encoding='utf-8', xml_declaration=True)
    
    print(f"XML exported successfully to: {target_path}")

if __name__ == "__main__":
    # מאפשר הרצה מהירה לבדיקה של הקובץ בלבד
    print("xml_exporter module is ready.")