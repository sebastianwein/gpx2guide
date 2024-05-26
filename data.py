import gpxpy
from scipy.optimize import root
from units import *


class GeoData:

    def __init__(self, lat, lon, x, y, dist):
        if not lat.size == lon.size == x.size == y.size == dist.size: raise TypeError
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.dist = dist
        self.len = lat.size

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


    def segment(self, dx: float, dy: float):

        geo_data = list()
        prev_idx = 0

        while True:

            lat = self.lat[prev_idx:]
            lon = self.lon[prev_idx:]
            x = self.x[prev_idx:]
            y = self.y[prev_idx:]
            dist = self.dist[prev_idx:]
            if prev_idx > 0:
                lat = np.insert(lat, 0, geo_coord0.lat)
                lon = np.insert(lon, 0, geo_coord0.lon)
                x = np.insert(x, 0, mercator_coord0.x)
                y = np.insert(y, 0, mercator_coord0.y)
                dist = np.insert(dist, 0, dist0)
            xmin = np.minimum.accumulate(x)
            xmax = np.maximum.accumulate(x)
            ymin = np.minimum.accumulate(y)
            ymax = np.maximum.accumulate(y)
            xspan = xmax - xmin
            yspan = ymax - ymin
            i = np.argmax(xspan > dx)
            j = np.argmax(yspan > dy)
            if i == 0 and j == 0: break 
            idx = min(i, j) if i>0 and j>0 else max(i, j)

            xspan1 = xspan[idx-1]
            yspan1 = yspan[idx-1]
            xspan2 = xspan[idx]
            yspan2 = yspan[idx]
            mercator_coord2 = MercatorCoord(x[idx], y[idx])
            mercator_coord1 = MercatorCoord(x[idx-1], y[idx-1])
            # interpolating x0, y0 such that xspan0 = dx or yspan0 = dy
            t = (xspan2 - dx)/(xspan2 - xspan1) if idx == i else (yspan2 - dy)/(yspan2 - yspan1)
            mercator_coord0 = mercator_coord2 - t*(mercator_coord2-mercator_coord1)

            geo_coord1 = mercator_coord1.to_geo()
            geo_coord0 = mercator_coord0.to_geo()
            dist0 = dist[idx-1] + geo_coord1.dist(geo_coord0)
            lat = np.append(lat[:idx], geo_coord0.lat)
            lon = np.append(lon[:idx], geo_coord0.lon)
            x = np.append(x[:idx], mercator_coord0.x)
            y = np.append(y[:idx], mercator_coord0.y)
            dist = np.append(dist[:idx], dist0)
            geo_data.append(GeoData(lat, lon, x, y, dist))

            prev_idx += idx-1

        if prev_idx == self.len-1: return geo_data

    
        lat = np.insert(self.lat[prev_idx:], 0, geo_coord0.lat)
        lon = np.insert(self.lon[prev_idx:], 0, geo_coord0.lon)
        x = np.insert(self.x[prev_idx:], 0, mercator_coord0.x)
        y = np.insert(self.y[prev_idx:], 0, mercator_coord0.y)
        dist = np.insert(self.dist[prev_idx:], 0, dist0)
        geo_data.append(GeoData(lat, lon, x, y, dist))

        return geo_data

    
    def find_dist(self, dist: float, interpolate: bool=True) -> GeoCoord:
        i = np.argmax(self.dist > dist)
        if i == 0: return None
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
    data = GeoData.from_gpx("gpx\jakobswege.gpx")
    geo_data = data[0]
    d = geo_data.segment(0.0005, 0.0005)
    for a in d:
        print(a.x, a.y)