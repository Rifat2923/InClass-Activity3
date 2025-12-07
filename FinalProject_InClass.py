 
import arcpy
import ee
import geopandas as gpd
import pandas as pd
from pathlib import Path

 
ee.Initialize()

def add_elevation_to_shapefile(shapefile_path, dem_dataset='USGS/3DEP/10m'):
     
    shapefile_path = Path(shapefile_path)
    if not shapefile_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")
 
    field_names = [f.name for f in arcpy.ListFields(shapefile_path)]
    if 'elevation' not in field_names:
        arcpy.management.AddField(shapefile_path, 'elevation', 'FLOAT')
        print("Added 'elevation' field")

     
    geom_list = []
    with arcpy.da.SearchCursor(shapefile_path, ['SHAPE@XY']) as cursor:
        for row in cursor:
            x, y = row[0]
             
            point = arcpy.PointGeometry(arcpy.Point(x, y), arcpy.Describe(shapefile_path).spatialReference)
            point_wgs84 = point.projectAs(arcpy.SpatialReference(4326))
            geom_list.append(ee.Geometry.Point([point_wgs84.centroid.X, point_wgs84.centroid.Y]))

    print(f"Collected {len(geom_list)} points from shapefile")

     
    dem = ee.Image(dem_dataset)
    fc = ee.FeatureCollection(geom_list)
    sampled = dem.sampleRegions(collection=fc, scale=10)  
    results = sampled.getInfo()['features']

     
    i = 0
    with arcpy.da.UpdateCursor(shapefile_path, ['elevation']) as cursor:
        for row in cursor:
            if i < len(results):
                elev_value = results[i]['properties'].get('elevation')
                row[0] = elev_value if elev_value is not None else -9999   
                cursor.updateRow(row)
            i += 1

    print(f"Successfully wrote elevation to {i} features")
    print("Done!")


def main():
    
    shp_path = r"E:\tmp\boundary1.shp"           
     

    add_elevation_to_shapefile(shp_path)


if __name__ == "__main__":
    main()

    def add_elevation_to_feature_class(input_fc, field_name="elevation"):
    
    import ee
    ee.Initialize()   

  
    if field_name not in [f.name for f in arcpy.ListFields(input_fc)]:
        arcpy.management.AddField(input_fc, field_name, "FLOAT")
        arcpy.AddMessage(f"Added field: {field_name}")

     
    geom_list = []
    sr = arcpy.Describe(input_fc).spatialReference
    with arcpy.da.SearchCursor(input_fc, ["SHAPE@XY"]) as cursor:
        for x, y in cursor:
            pt = arcpy.PointGeometry(arcpy.Point(x, y), sr).projectAs(arcpy.SpatialReference(4326))
            geom_list.append(ee.Geometry.Point([pt.centroid.X, pt.centroid.Y]))

    arcpy.AddMessage(f"Querying GEE for {len(geom_list)} points...")
    dem = ee.Image("USGS/3DEP/10m")
    fc = ee.FeatureCollection(geom_list)
    sampled = dem.sampleRegions(collection=fc, scale=10)
    results = sampled.getInfo()["features"]
 
    with arcpy.da.UpdateCursor(input_fc, [field_name]) as cursor:
        for i, row in enumerate(cursor):
            if i < len(results):
                elev = results[i]["properties"].get("elevation")
                row[0] = elev if elev is not None else -9999
                cursor.updateRow(row)

    arcpy.AddMessage("All done! Elevation values added.")