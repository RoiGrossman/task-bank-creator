import sys
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent / "0-project-root"
sys.path.append(str(BASE_DIR))

from src import raw_polygons_processor, priority_shuffler, raw_shp_to_xml, add_constraints

def main():
    print("\n--- Target Generator Main Menu ---")
    print("1. Process Raw Polygons")
    print("2. Shuffle Priorities")
    print("3. Convert SHP to XML")
    print("4. Add Constraints")
    
    choice = input("\nSelect an option [1-4]: ").strip()

    not_strategy_data = input("Export as Strategy .xml? (y/n) [default: n]: ").lower()
    os.environ['STRATEGY_XML'] = 'false' if not_strategy_data == 'y' else 'true'
    
    if choice == '1':
        print("Running Process Raw Polygons...")
        raw_polygons_processor.main()
    elif choice == '2':
        print("Running Shuffle Priorities...")
        priority_shuffler.main()
    elif choice == '3':
        print("Running Convert SHP to XML...")
        raw_shp_to_xml.main()
    elif choice == '4':
        print("Running Add Constraints...")
        add_constraints.main()
    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()