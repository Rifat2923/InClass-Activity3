
import arcpy
import os
import sys

class Toolbox(object):
    def __init__(self):
        self.label = "GEE Elevation Tools"
        self.alias = "gee"
        self.tools = [AddElevationTool]


class AddElevationTool(object):
    def __init__(self):
        self.label = "1. Add Elevation from Google Earth Engine (10m)"
        self.description = "Adds 10m USGS 3DEP elevation from GEE to point features"
        self.canRunInBackground = False

    def getParameterInfo(self):
        p0 = arcpy.Parameter(
            displayName="Input Point Features",
            name="in_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        p0.filter.list = ["Point"]

        p1 = arcpy.Parameter(
            displayName="Elevation Field Name",
            name="field_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        p1.value = "elevation"

        return [p0, p1]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        in_fc     = parameters[0].valueAsText
        field     = parameters[1].valueAsText or "elevation"

        
        import ee
        try:
            ee.Initialize()
        except Exception as e:
            arcpy.AddError("Earth Engine not authenticated. Run 'earthengine authenticate' in Anaconda Prompt first.")
            raise

   
        if field not in [f.name for f in arcpy.ListFields(in_fc)]:
            arcpy.management.AddField(in_fc, field, "FLOAT")
            arcpy.AddMessage(f"Created field: {field}")

         
        points = []
        sr = arcpy.Describe(in_fc).spatialReference
        with arcpy.da.SearchCursor(in_fc, ["SHAPE@XY"]) as cur:
            for x, y in cur:
                pt = arcpy.PointGeometry(arcpy.Point(x, y), sr).projectAs(arcpy.SpatialReference(4326))
                points.append(ee.Geometry.Point([pt.centroid.X, pt.centroid.Y]))

        arcpy.AddMessage(f"Downloading elevation for {len(points)} points from Google Earth Engine...")
        
        dem = ee.Image("USGS/3DEP/10m")
        fc = ee.FeatureCollection(points)
        result = dem.sampleRegions(collection=fc, scale=10).getInfo()["features"]

         
        with arcpy.da.UpdateCursor(in_fc, [field]) as cur:
            for i, row in enumerate(cur):
                elev = result[i]["properties"].get("elevation")
                row[0] = elev if elev is not None else -9999
                cur.updateRow(row)

        arcpy.AddMessage("Finished! Elevation added to all points.")