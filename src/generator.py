import geopandas as geopd
import hexcover

from shapely.geometry import Point, MultiPoint, LineString


def generate_data(coordinates, radius, grid=False, num_receivers=20):

    # Central point of central polygon
    # Default spatial reference system for GeoJSON: EPSG:4326 (Google Maps, OpenStreetMap...)
    # Spatial reference system for Croatia: EPSG:3765
    # Coordinates (45.762680, 15.999007) projected in EPSG:3765
    # Latitude and longitude positions are "inversed": see EPSG:4326 specification
    antenna = Point(coordinates[1], coordinates[0])
    antenna = geopd.GeoSeries(antenna)
    antenna.crs = "EPSG:4326"
    antenna = antenna.to_crs("EPSG:3765")[0]

    # Hexcover method for coverage returns a named tuple of seven shapely polygons
    # First polygon is always the central one
    hexagons = hexcover.hexagon_coverage(antenna, radius)
    sites = geopd.GeoSeries(hexagons)
    sites.crs = "EPSG:3765"

    # Central points of each site
    # First centroid has the same value as antenna
    centroids = sites.centroid

    # Plot data
    """
    import matplotlib.pyplot as plt
    ax = sites.plot(color="blue", alpha=0.8)
    centroids.plot(ax=ax, color="red", alpha=1.0)
    plt.show()
    """

    # Receives can be generated as a grid or uniformly on a line
    # from antenna to site edge
    receivers = []

    if grid:
        import numpy as np
        site_bounds = sites[0].bounds
        minx, miny = site_bounds[0], site_bounds[1]
        maxx, maxy = site_bounds[2], site_bounds[3]

        x_ax = np.linspace(minx, maxx, num=num_receivers)
        y_ax = np.linspace(miny, maxy, num=num_receivers)
        xv, yv = np.meshgrid(x_ax, y_ax, sparse=False, indexing="ij")

        for i in range(len(x_ax)):
            for j in range(len(y_ax)):
                receiver = Point(xv[i, j], yv[i, j])
                if sites[0].contains(receiver):
                    receivers.append(receiver)

    else:
        site_edge = MultiPoint(sites[0].boundary.coords)[0]
        path = LineString([centroids[0], site_edge])
        path_length = path.length
        path_increment = path_length // num_receivers

        for i in range(num_receivers):
            receiver = path.interpolate(path_increment * i)
            receivers.append(receiver)

    receivers = geopd.GeoSeries(receivers)
    receivers.crs = "EPSG:3765"

    results = {
        "antenna": antenna,
        "sites": sites,
        "centroids": centroids,
        "receivers": receivers
    }

    complete_data = sites.append(centroids).append(receivers)
    complete_data.crs = "EPSG:3765"
    complete_data = complete_data.to_crs("EPSG:4326")
    complete_data.to_file("../data.geojson", driver="GeoJSON")

    return results
