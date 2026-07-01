import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import uuid

# Paths and base directories

def export_to_xml(gdf, output_xml_path):
    target_path = Path(output_xml_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    root = ET.Element("message", {
        "xmlns": "http://scc/xml/schemas",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://scc/xml/schemas V:sccXSD_Message.xsd"
    })
    
    # Header
    icc_header = ET.SubElement(root, "iccHeader")
    ET.SubElement(icc_header, "messageType").text = "MissionRequirements"
    ET.SubElement(icc_header, "originator").text = "foo"
    ET.SubElement(icc_header, "originatorAddress").text = "foo-bar"
    ET.SubElement(icc_header, "recipient").text = "bar-foo"
    now = datetime.now()
    ET.SubElement(icc_header, "creationTime").text = str(int(now.timestamp()))
    ET.SubElement(icc_header, "creationTimeString").text = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    
    # Mission Data
    mission_data = ET.SubElement(root, "missionRequirementsData")
    ET.SubElement(mission_data, "satellite").text = "OF7"
    ET.SubElement(mission_data, "scowId").text = "Foo#10225#BAR#-#1"
    ET.SubElement(mission_data, "planRequirementId").text = "1693___1720"
    ET.SubElement(mission_data, "updatedRequirementList").text = "false"
    
    req_list = ET.SubElement(mission_data, "requirementList")
    
    for _, row in gdf.iterrows():
        req = ET.SubElement(req_list, "requirement")
        
        # Requirement data
        requirement_id = str(row.get('id')) if row.get('id') else str(uuid.uuid4())
        ET.SubElement(req, "palRequirementId").text = requirement_id
        requirement_name = str(row.get('name')) if row.get('name') else str("TestReq")
        ET.SubElement(req, "requirementName").text = requirement_name
        ET.SubElement(req, "type").text = "Standing"
        ET.SubElement(req, "extraRequirement").text = "false"
        ET.SubElement(req, "deleted").text = "false"
        ET.SubElement(req, "priority").text = str(row.get('priority', '5'))
        ET.SubElement(req, "unPlannedElsewhere").text = "false"
        ET.SubElement(req, "plannedElsewhere").text = "false"
        ET.SubElement(req, "disseminationPriority").text = "7"
        ET.SubElement(req, "worstAcceptableResolution").text = "1"
        ET.SubElement(req, "cloudCoverageForcast").text = "0"
        ET.SubElement(req, "percentUnusableData").text = "20"
        ET.SubElement(req, "displayText").text = "No Comments"
        
        # Target Image Data
        target_data = ET.SubElement(req, "targetImageData")
        ET.SubElement(target_data, "targetCenterHeight").text = "500"
        poly_boundary = ET.SubElement(target_data, "polygonBoundary")
        if row.geometry and row.geometry.geom_type == 'Polygon':
            for coord in list(row.geometry.exterior.coords):
                pt = ET.SubElement(poly_boundary, "geographicPoint")
                ET.SubElement(pt, "long").text = f"{coord[0]:.6f}"
                ET.SubElement(pt, "lat").text = f"{coord[1]:.6f}"
                ET.SubElement(pt, "heightUnknown")
        
        ET.SubElement(target_data, "nominalTargetGroundContrast")
        ET.SubElement(target_data, "niirsNotApplicable")
        
        # End of Requirement fields
        ET.SubElement(req, "desirability").text = "7"
        ET.SubElement(req, "anchor").text = "true"
        ET.SubElement(req, "monoImaging")
        
        # Constraints
        cons = ET.SubElement(req, "coverageConstraints")
        ET.SubElement(cons, "oneScan").text = "true"
        ET.SubElement(cons, "oneScow").text = "false"
        
        # Time Constraints
        time_cons = ET.SubElement(req, "timeConstraints")
        dates = ET.SubElement(time_cons, "imagingDates")
        range_el = ET.SubElement(dates, "dateRange")
        ET.SubElement(range_el, "start").text = "2011-06-05T00:00:00.000"
        ET.SubElement(range_el, "end").text = "2013-01-01T01:00:00.000"
        ET.SubElement(time_cons, "noImagingTimes")
    
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(target_path, encoding='utf-8', xml_declaration=True)