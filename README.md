**TARGET GENERATOR**

Automation scripts to prioritize and manipulate raw GeoJson files into MBT SCC targets XML

This project is based on Shir Ben Ami's initial efforts

Most of the code, logics and functions are AI generated, T.L.H 



TABLE OF CONTENTS:

1\. Formal Definitions

&#x09;- Structure

&#x09;- System Requrements

&#x09;- Install and run

&#x09;- Main components



2\. Workflow Overview





────────────────────────────────────────────────────────────────

**Formal Definitions**



\# Structure

Task bank creator/

├── main.py           	   # Run this to use project

├── 1-raw\_OSM\_exports/

├── 2-data/               

│   ├── raw/              # Inputs - export.geojson, AOI.kml

│   └── processed/        # Outputs

├── 3-docs/		   # Includes the MBT SCC target xml schema

├── src/                  # Scripts

│   ├── \_\_init\_\_.py

│   ├── xml\_exporter.py

│   ├── priority\_shuffler.py

│   └── raw\_polygons\_processor.py





\# System requirements

\- Python 3.10+



\# Install and run

1\. Open the terminal in 'Task bank creator'

2\.  Create a VM:

&#x20;  ```bash

&#x20;  python -m venv .venv

&#x20;  .venv\\Scripts\\activate

3\. install requirements:

&#x20;  pip install -r requirements.txt

4\. run main:

&#x20;  python main.py





**Main components:**

**raw\_polygons\_processor.py** - Initial sort, clean and prioritization of given an input GeoJson



**priority\_shuffler.py -** Reprioritize of the basic output from raw\_polygons\_processor.py by constraints (e.g. prioritize clustered polygons over scattered)



**raw\_shp\_to\_xml.py -** Direct conversion of ShapeFiles (shp, shx,cpg, dbf, prj) to SCC targets XML format

────────────────────────────────────────────────────────────────



─────────────────────────────────────────────────────────────────────────────────────



**Workflow Overview**

\----------------------------------

Data Extraction (Overpass Turbo)



1. **Visit** [https://overpass-turbo.eu/](https://overpass-turbo.eu/)

**2. Query:**

**(note: play with the timeout as a dependance of your query, some are just to big for the browser query)**

**(note: visit** [**OSM wiki**](https://wiki.openstreetmap.org/wiki/Map_features#Common_landuse_key_values_-_developed_land) **to find possible query categories to fit you need in terms of shape size and amount, I found 'quarry' to be good enough)**



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



3\. click **RUN**

**(note: If a "Large amount of data" warning appears, click Continue. If the server is busy, wait 10 seconds and try again)**



**4. Once the map populates, click Export in the top menu.**



**5. Under the Data section, select download GeoJSON.**



**6. Save the downloaded file as export.geojson under 'Task bank creator\\2-data\\raw'.**



**(note: If you want to filter only a certain Area Of Interest from the entire country (e.g. USA) Visit** [**Google My Maps**](https://www.google.com/maps/d/) **and draw your AOI Polygon, when exporting hit 'Export to KML/KMZ' and then choose 'Export as KML instead of KMZ'. Save the downloaded file as AOI.KLM under 'Task bank creator\\2-data\\raw')**

**(note: use 'Task bank creator\1-raw_OSM_exports' to save old exports that may be useful in the future)



\----------------------------------



\----------------------------------

**Initial manipulation of 'export.GeoJson'**

(important note! in our priority semantics 'the lower the better' -> 1 is the most important ptiority)



1. Run main.py and choose '1. Process Raw Polygons'
2. The script will filter out lines and dots, remove exact duplicate geometries
3. The script will ask you what priority range you want
4. The script will ask you how many targets you want to keep
5. The script will ask you whether when filtering you want a random or deterministic choosing between all available polygons
6. The script will ask you and the assign the priority distribution, choose between Normal distribution(bell curve)\\Uniform\\Linear ascending(few important targets, more and more as the priority rises)
7. The script will ask you how many lines you want to present in the summary file
8. The script will assign every Polygon with a UUID
9. The script will save all Polygons to an xml file in the SCC target schema
10. The script will overwrite and save all outputs to 'Task bank creator\\2-data\\processed\\output\_targets'

    1. prioritized\_targets.shape\_files (cpg, dbf, prj, shp, shx)
    2. summary.txt
    3. tasks\_baseline.xml

\----------------------------------



\----------------------------------

**Reorganize priorities of prioritized\_targets**



1. Run main.py and choose '2. **priority\_shuffler.py**'
2. The script will use the current shape files in output\_targets
3. The script will ask you how you want to re-prioritize

   1. Randomly
   2. Invert priorities between 1-10, 2-9...
   3. Make the most distanced Polygons more important
   4. Make cluster targets more important (important note! **THIS FUNCTION DOES'NT WORK**! I do this manually with QGIS, good luck)
   5. The script will open a new folder under 'Task bank creator\\2-data\\processed' and paste the new\&updated  versions of the shapefiles and SCC xml

\----------------------------------



\----------------------------------

**Manually prioritizing tasks with QGIS**



If you had to manually prioritize using QGIS 

1. save the updated .shp file under 'Task bank creator\\2-data\\processed\\output\_targets' alongside the other shapefiles and run main.py
2. Choose 3. Convert SHP to XML
3. The script will ask you where to run, copy the .shp file as path and paste in the terminal, the script export a new SCC formatted xml in 'Task bank creator\\2-data\\processed\\output\_targets' named 'prioritized\_targets'

\----------------------------------



\----------------------------------



**Visualization \& Verification (Mapshaper)**



1. Open [mapshaper](https://mapshaper.org/)
2. Drag\&Drop AOI.kml for reference
3. Drag\&Drop all shapefiles from 'Task bank creator\\2-data\\processed\\output\_targets'
4. Choose a base map from the top-right corner if it is more comfortable
5. To inspect polygon priorities hover over the mouse button in the top right corner (under the home,+,-), then click 'inspect features'

















&#x09;	





































