**TARGET GENERATOR**

Automation scripts to prioritize and manipulate raw GeoJson files into MBT SCC targets XML

This project is based on Shir Ben Ami's initial efforts

Most of the code, logics and functions are AI generated, T.L.H 



TABLE OF CONTENTS:

1. Formal Definitions

	- Structure

	- System Requrements

	- Install and run

	- important notes


2. Workflow Overview
	- Data extractions

	- Initial manipulations of the GeoJSON

	- Reorganize priorities by predefined logic sets

	- Manually prioritizing tasks with QGIS (if needed)

	- Visualization & Verification (if needed)

	- Manually make a single constrained task

	- Add constraints to a target bank

────────────────────────────────────────────────────────────────

Formal Definitions



# Structure

Task_bank_creator

├── main.py           	   # Run this to use project

├── 1-raw_OSM_exports/

├── 2-data/               

│   ├── raw/              # Inputs - export.geojson, AOI.kml

│   └── processed/        # Outputs - Initial output_targets, Advanced manipulation folders, Manually saved xml versions

├── 3-docs/		  # Includes the MBT SCC target xml schema etc.

├── old/		  # Manually saved old files

├── src/                  # Scripts

│   ├── __init__.py

│   ├── xml_exporter.py		    # This is the function other scripts call to turn .shp files into .xml

│   ├── priority_shuffler.py	    # Use this to manipulate priorities based on some pre-defined options (from output_targets)

│   └── raw_polygons_processor.py   # Use this first, to turn a big GeoJson export into .shp and .xml files

│   └── raw_shp_to_xml.py 	    # Use this to convert any .shp output from manual QGIS edits

│   └── add_constraints.py	    # Use this to add advanced constraints on big target banks (from output_targets)

├── web_interface/

│   └── index.html		    # This .html allows the user manually export targets with advanced constraints to .xml

├── api.py			    # This .py mitigates the data from index.html's interface to xml_exporter 









# System requirements

	- Python 3.10+
	- Installations from requirements.txt




# Install and run

	1. Open the terminal in 'Task_bank_creator'

	2. Create a VM:

	    ```bash

	    python -m venv .venv

	   .venv\\Scripts\\activate

	3. install requirements:

	   pip install -r requirements.txt

	4. run main:

	   python main.py




────────────────────────────────────────────────────────────────
# important notes

(Important note! in our priority semantics 'the lower the better' -> 1 is the most important ptiority)
(
	Important note! the scripts will ask you if you want to export as Strategy xml,
	if you choose 'yes', the scema will integrate into Strategy as a target bank, but will only include a few constraint fields
		name
		id
		priority
		resolution
		date range
	those constraints will NOT be included
		scan azimuth
		scan length
		SAT azimuth
		elevation
		time in day
)
────────────────────────────────────────────────────────────────

**Workflow Overview**
\----------------------------------

Data Extraction (Overpass Turbo)



	1. Visit https://overpass-turbo.eu/ 

	2. Query:

		(note: play with the timeout as a dependance of your query, some are just to big for the browser query)**

		(note: visit OSM wiki: https://wiki.openstreetmap.org/wiki/Map_features#Common_landuse_key_values_-_developed_land to find possible query categories to fit you need in terms of shape size and amount, I found 'quarry' to be good enough)



\[out:json]\[timeout:300];

(

&#x20; {{geocodeArea:United States}}->.a;

);

(

&#x20; nwr\[landuse=quarry](area.a);

);

out body;

>;

out geom;



	3. click RUN

	(note: If a "Large amount of data" warning appears, click Continue. If the server is busy, wait 10 seconds and try again)



	4. Once the map populates, click Export in the top menu.



	5. Under the Data section, select download GeoJSON.



	6. Save the downloaded file as export.geojson under 'Task_bank_creator\2-data\raw'.

	(note: If you want to filter only a certain Area Of Interest from the entire country (e.g. USA) Visit Google My Maps: https://www.google.com/maps/d/ and draw your AOI Polygon, when exporting hit 'Export to KML/KMZ' and then choose 'Export as KML instead of KMZ'. Save the downloaded file as AOI.KLM under 'Task_bank_creator\2-data\raw')

(note: use 'Task_bank_creator\1-raw_OSM_exports' to save old exports that may be useful in the future)

\----------------------------------



\----------------------------------

Initial manipulation of 'export.GeoJson' (raw_polygons_processor.py)

	1. Run main.py and choose '1. Process Raw Polygons'
	2. The script will filter out lines and dots, remove exact duplicate geometries
	3. The script will ask you what priority range you want
	4. The script will ask you how many targets you want to keep
	5. The script will ask you whether when filtering you want a random or deterministic choosing between all available polygons
	6. The script will ask you and the assign the priority distribution, choose between Normal distribution(bell curve)\\Uniform\\Linear ascending(few important targets, more and more as the priority rises)
	7. The script will ask you how many lines you want to present in the summary file
	8. The script will assign every Polygon with a UUID
	9. The script will save all Polygons to an xml file in the SCC target schema
	10. The script will overwrite and save all outputs to 'Task_bank_creator\2-data\processed\output_targets'

    	1. prioritized\_targets.shape\_files (cpg, dbf, prj, shp, shx)
    	2. summary.txt
    	3. tasks\_baseline.xml

\----------------------------------



\----------------------------------

Reorganize priorities of prioritized_targets (priority_shuffler.py)

1. Run main.py and choose '2. **priority\_shuffler.py**'
2. The script will use the current shape files in output\_targets
3. The script will ask you how you want to re-prioritize

   1. Randomly
   2. Invert priorities between 1-10, 2-9...
   3. Make the most distanced Polygons more important
   4. Make cluster targets more important (important note! **THIS FUNCTION DOES'NT WORK**! I do this manually with QGIS, good luck)
   5. The script will open a new folder under 'Task_bank_creator\2-data\processed' and paste the new\&updated  versions of the shapefiles and SCC xml

\----------------------------------



\----------------------------------

Manually prioritizing tasks with QGIS

If you had to manually prioritize using QGIS 

	1. save the updated .shp file under 'Task_bank_creator\2-data\processed\output\_targets' alongside the other shapefiles and run main.py
	2. Choose 3. Convert SHP to XML
	3. The script will ask you where to run, copy the .shp file as path and paste in the terminal, the script export a new SCC formatted xml in 'Task_bank_creator\2-data\processed\output_targets' named 'prioritized_targets'

\----------------------------------



\----------------------------------

Visualization & Verification (Mapshaper)

	1. Open [mapshaper](https://mapshaper.org/)
	2. Drag\&Drop AOI.kml for reference
	3. Drag\&Drop all shapefiles from 'Task_bank_creator\2-data\processed\\output\_targets'
	4. Choose a base map from the top-right corner if it is more comfortable
	5. To inspect polygon priorities hover over the mouse button in the top right corner (under the home,+,-), then click 'inspect features'

\----------------------------------



\----------------------------------

Manually make a single constrained task (index.html + api.py)

	1. Open terminal in the project directory (Task_bank_creator)
	2. Run this command: Task_bank_creator>uvicorn api:app --reload
	3. Open index.html (http://127.0.0.1:*port number*)
	4. Set your desired polygon and add your constraints
	5. Hit 'Export to XML'
	6. The xml will be saved to your local 'Downloads' folder, as well as in Task_bank_creator\2-data\processed\xml_ready_taskfiles\manual_exports

(important note! **Most of the data fields are currently only implemented into the a non-Strategy schema of the .xml**!)

\----------------------------------



\----------------------------------

Add constraints to a target bank (add_constraints.py)

	1. Run through Main.py
	2. The script imports Task_bank_creator\2-data\processed\output_targets as it's base input
	3. Choose constraint and how to implement it, you can add more than one constraint and you can add a constraint as a dependency of another constraint
	4. The output files will be exported to Task_bank_creator\2-data\processed\__New_Directory__































