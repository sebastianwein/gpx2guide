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
        func = lambda a: a[0].dist(a[1])
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
    
    def append(self, other):
        self.lat = np.append(self.lat, other.lat)
        self.lon = np.append(self.lon, other.lon)
        self.x = np.append(self.x, other.x)
        self.y = np.append(self.y, other.y)
        self.dist = np.append(self.dist, other.dist)
    
    def min(self) -> GeoCoord:
        return GeoCoord(np.min(self.lat), np.min(self.lon))
    def max(self) -> GeoCoord:
        return GeoCoord(np.max(self.lat), np.max(self.lon))
    def mean(self) -> GeoCoord:
        return (self.min() + self.max())/2


    def segment(self, delta_x: float, delta_y: float):

        delta1, delta2 = sorted([delta_x, delta_y])

        geo_data = list()
        prev_idx = 0

        while True:

            lat = self.lat[prev_idx:]
            lon = self.lon[prev_idx:]
            x = self.x[prev_idx:]
            y = self.y[prev_idx:]
            dist = self.dist[prev_idx:]
            # Inserting previously interpolated coordinate
            if prev_idx > 0:
                lat = np.insert(lat, 0, geo_coord_interp.lat)
                lon = np.insert(lon, 0, geo_coord_interp.lon)
                x = np.insert(x, 0, mercator_coord_interp.x)
                y = np.insert(y, 0, mercator_coord_interp.y)
                dist = np.insert(dist, 0, dist_interp)
            xspan = np.maximum.accumulate(x) - np.minimum.accumulate(x)
            yspan = np.maximum.accumulate(y) - np.minimum.accumulate(y)
            i = np.argmax(xspan > delta1)
            j = np.argmax(yspan > delta1)
            if i == 0 and j == 0: break 
            idx = min(i, j) if i>0 and j>0 else max(i, j)
            delta_x = delta2 if idx == i else delta1
            delta_y = delta1 if idx == i else delta2
            i = np.argmax(xspan > delta_x)
            j = np.argmax(yspan > delta_y)
            idx = min(i, j) if i>0 and j>0 else max(i, j)

            xspan1 = xspan[idx-1]
            yspan1 = yspan[idx-1]
            xspan2 = xspan[idx]
            yspan2 = yspan[idx]
            mercator_coord2 = MercatorCoord(x[idx], y[idx])
            mercator_coord1 = MercatorCoord(x[idx-1], y[idx-1])
            # Interpolating x0, y0 such that xspan0 = dx or yspan0 = dy
            t = (xspan2 - delta_x)/(xspan2 - xspan1) if idx == i else (yspan2 - delta_y)/(yspan2 - yspan1)
            mercator_coord_interp = mercator_coord2 - t*(mercator_coord2-mercator_coord1)

            geo_coord1 = mercator_coord1.to_geo()
            geo_coord_interp = mercator_coord_interp.to_geo()
            dist_interp = dist[idx-1] + geo_coord1.dist(geo_coord_interp)
            lat = np.append(lat[:idx], geo_coord_interp.lat)
            lon = np.append(lon[:idx], geo_coord_interp.lon)
            x = np.append(x[:idx], mercator_coord_interp.x)
            y = np.append(y[:idx], mercator_coord_interp.y)
            dist = np.append(dist[:idx], dist_interp)
            geo_data.append(GeoData(lat, lon, x, y, dist))

            if prev_idx == 0: prev_idx = idx
            else: prev_idx += idx-1

        if prev_idx == self.len-1: return geo_data

        lat = np.insert(self.lat[prev_idx:], 0, geo_coord_interp.lat)
        lon = np.insert(self.lon[prev_idx:], 0, geo_coord_interp.lon)
        x = np.insert(self.x[prev_idx:], 0, mercator_coord_interp.x)
        y = np.insert(self.y[prev_idx:], 0, mercator_coord_interp.y)
        dist = np.insert(self.dist[prev_idx:], 0, dist_interp)
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
        geo_coord_interp = geo_coord2 - t*(geo_coord2-geo_coord1)
        return geo_coord_interp


if __name__ == "__main__":
    data = GeoData.from_gpx("gpx\jakobswege.gpx")
    geo_data = data[0]
    d = geo_data.segment(0.0005, 0.0005)
    for a in d:
        print(a.x, a.y)