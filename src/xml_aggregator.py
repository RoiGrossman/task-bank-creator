import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import copy

# הגדרת נתיבי הקלט והפלט
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "2-data" / "task_files_aggregator" / "input"
OUTPUT_DIR = BASE_DIR / "2-data" / "task_files_aggregator" / "output"

def strip_namespaces(el):
    """
    פונקציה רקורסיבית שמנקה את מרחבי השמות (namespaces) 
    מכל התגיות באובייקט כדי ש-ElementTree לא יוסיף קידומות כמו ns0:
    """
    if type(el.tag) is str and '}' in el.tag:
        el.tag = el.tag.split('}', 1)[1]
    for child in el:
        strip_namespaces(child)

def create_base_xml_structure():
    """מייצר את המעטפת הבסיסית בתגיות נקיות"""
    root = ET.Element("message", {
        "xmlns": "http://scc/xml/schemas",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://scc/xml/schemas V:sccXSD_Message.xsd"
    })
    
    icc_header = ET.SubElement(root, "iccHeader")
    ET.SubElement(icc_header, "messageType").text = "MissionRequirements"
    ET.SubElement(icc_header, "originator").text = "foo"
    ET.SubElement(icc_header, "originatorAddress").text = "foo-bar"
    ET.SubElement(icc_header, "recipient").text = "bar-foo"
    now = datetime.now()
    ET.SubElement(icc_header, "creationTime").text = str(int(now.timestamp()))
    ET.SubElement(icc_header, "creationTimeString").text = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    
    mission_data = ET.SubElement(root, "missionRequirementsData")
    ET.SubElement(mission_data, "satellite").text = "OF7"
    ET.SubElement(mission_data, "scowId").text = "Foo#10225#BAR#-#1"
    ET.SubElement(mission_data, "planRequirementId").text = "1693___1720"
    ET.SubElement(mission_data, "updatedRequirementList").text = "false"
    
    req_list = ET.SubElement(mission_data, "requirementList")
    
    return root, req_list

def main():
    print("\n--- Running XML Aggregator ---")
    
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    xml_files = list(INPUT_DIR.glob("*.xml"))
    
    if not xml_files:
        print(f"No XML files found in {INPUT_DIR}. Please add files and try again.")
        return

    # --- שלב 1: סריקה, איסוף אובייקטים והכנת דוח ---
    print("Scanning input directory...\n")
    
    files_data = [] # רשימה שתשמור מילונים עם שם הקובץ והאובייקטים שלו
    total_requirements = 0
    ns = {'scc': 'http://scc/xml/schemas'}

    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            file_root = tree.getroot()
            
            # חיפוש האובייקטים בקובץ
            requirements = file_root.findall('.//scc:requirement', namespaces=ns)
            if not requirements:
                requirements = file_root.findall('.//requirement')

            files_data.append({
                'name': xml_file.name,
                'requirements': requirements
            })
            total_requirements += len(requirements)
                
        except ET.ParseError as e:
            print(f"\n[ERROR] Malformed XML file detected in {xml_file.name}!")
            print(f"Error details: {e}")
            print("Aggregation aborted. Please fix the file and run again.")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Unexpected error processing {xml_file.name}: {e}")
            sys.exit(1)

    # הצגת הדוח למשתמש
    print("--- Input Summary ---")
    for data in files_data:
        print(f" - {data['name']}: {len(data['requirements'])} requirement(s)")
    print("---------------------")
    print(f"Total files: {len(xml_files)}")
    print(f"Total requirements to aggregate: {total_requirements}")

    if total_requirements == 0:
        print("\nNo <requirement> objects found in any of the input files. Exiting.")
        return

    # --- שלב 2: בקשת אישור מהמשתמש ---
    user_approval = input("\nDo you want to proceed with aggregation? (y/n) [default: y]: ").strip().lower()
    
    if user_approval == 'n':
        print("Aggregation aborted by user.")
        return

    # --- שלב 3: איחוד בפועל ויצירת הקובץ החדש ---
    print("\nAggregating...")
    root, main_req_list = create_base_xml_structure()
    
    for data in files_data:
        for req in data['requirements']:
            clean_req = copy.deepcopy(req)
            strip_namespaces(clean_req)  # ניקוי שאריות לפני ההכנסה לעץ החדש
            main_req_list.append(clean_req)

    # שמירת הקובץ
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"aggregated_targets_{timestamp}.xml"
    output_path = OUTPUT_DIR / output_filename
    
    output_tree = ET.ElementTree(root)
    ET.indent(output_tree, space="    ", level=0)
    output_tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\nSuccess! Aggregated {total_requirements} requirements.")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()