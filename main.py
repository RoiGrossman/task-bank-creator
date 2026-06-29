import sys
from pathlib import Path

# עכשיו אנחנו בתיקיית האב, ה-src נמצא בתוך 0-project-root
# אז ה-BASE_DIR שלנו הוא 0-project-root
BASE_DIR = Path(__file__).resolve().parent / "0-project-root"
sys.path.append(str(BASE_DIR))

from src import raw_polygons_processor, priority_shuffler, raw_shp_to_xml

def main():
    print("\n--- Target Generator Main Menu ---")
    print("1. Process Raw Polygons")
    print("2. Shuffle Priorities")
    print("3. Convert SHP to XML")
    
    choice = input("\nSelect an option [1-3]: ").strip()
    
    if choice == '1':
        raw_polygons_processor.main()
    elif choice == '2':
        priority_shuffler.main()
    elif choice == '3':
        raw_shp_to_xml.main()
    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()