import gpxpy
from scipy.optimize import root
from units import *


class GeoData:

    def __init__(self, lat, lon, x, y, dist):
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.dist = dist

    @classmethod
    def from_geo(cls, geo_coords: list[GeoCoord]):
        lat = np.array([geo_coord.lat for geo_coord in geo_coords])
        lon = np.array([geo_coord.lon for geo_coord in geo_coords])
        x = np.array([geo_coord.to_mercator().x for geo_coord in geo_coords])
        y = np.array([geo_coord.to_mercator().y for geo_coord in geo_coords])
        func = lambda a: GeoCoord.dist(a[0], a[1])
        delta = np.insert(np.apply_along_axis(func, 1, np.column_stack((geo_coords[:-1], geo_coords[1:]))), 0, 0)
        dist = np.cumsum(delta)
        return cls(lat, lon, x, y, dist)

    @classmethod
    def from_gpx(cls, filename: str):

        geo_data = list()
        with open(filename, "r") as file:
            gpx = gpxpy.parse(file)
            for track in gpx.tracks:
                geo_coords = list()
                for segment in track.segments:
                    geo_coords.extend([GeoCoord(point.latitude, point.longitude) for point in segment.points])
                geo_data.append(cls.from_geo(geo_coords))
        
        return geo_data
    
    def min(self) -> GeoCoord:
        return GeoCoord(np.min(self.lat), np.min(self.lon))
    def max(self) -> GeoCoord:
        return GeoCoord(np.max(self.lat), np.max(self.lon))
    def mean(self) -> GeoCoord:
        return (self.min() + self.max())/2


    def fit_to_bounds(self, dx, dy):
        pass
    
    def find_dist(self, dist: float, interpolate: bool=True) -> GeoCoord:
        i = np.argmax(self.dist > dist)
        if i == 0: raise ValueError
        geo_coord1 = GeoCoord(self.lat[i-1], self.lon[i-1])
        geo_coord2 = GeoCoord(self.lat[i], self.lon[i])
        if not interpolate: return geo_coord2
        dist2 = self.dist[i]
        def error(t):
            error = (geo_coord2-t[0]*(geo_coord2-geo_coord1)).dist(geo_coord2) - (dist2-dist)
            return error
        t = np.abs(root(error, [0]).x[0])
        geo_coord = geo_coord2 - t*(geo_coord2-geo_coord1)
        return geo_coord


if __name__ == "__main__":
    print("hallo")
    data = GeoData.from_gpx("gpx\Dole_Salin-les-Bains.gpx")
    geo_data = data[0]
    print(geo_data.find_dist(40))