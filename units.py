import numpy as np


class GeoCoord:


    def __init__(self, lat: float, lon: float) -> None:
        self.lat = lat
        self.lon = lon
        self.phi = np.deg2rad(lat)
        self.lam = np.deg2rad(lon)
    
    def __repr__(self) -> str:
        return f"<GeoCoord lat:{self.lat}, lon:{self.lon}>"
    
    def __add__(self, other):
        return GeoCoord(self.lat+other.lat, self.lon+other.lon)
    
    def __sub__(self, other):
        return GeoCoord(self.lat-other.lat, self.lon-other.lon)
    
    def __rmul__(self, scalar: float):
        if isinstance(scalar, (int, np.integer)) or isinstance(scalar, (float, np.floating)):
            return GeoCoord(scalar*self.lat, scalar*self.lon)
        else:
            raise NotImplementedError

    def __truediv__(self, scalar: float):
        if isinstance(scalar, (int, np.integer)) or isinstance(scalar, (float, np.floating)):
            return GeoCoord(self.lat/scalar, self.lon/scalar)
        else:
            raise NotImplementedError


    def to_mercator(self):
        return MercatorCoord(self.geo2mercator_x(self.lon), self.geo2mercator_y(self.lat))
    
    def dist(self, other) -> float:
        return self.haversine_dist(self.phi, self.lam, other.phi, other.lam)


    # Mercator projection
    @staticmethod
    def geo2mercator_x(lon):
        lam = np.deg2rad(lon)
        x = lam
        return x
    @staticmethod
    def geo2mercator_y(lat):
        phi = np.deg2rad(lat)
        y = np.log(np.tan(phi/2 + np.pi/4))
        return y
    # Haversine distance formula
    @staticmethod
    def haversine_dist(phi1, lam1, phi2, lam2):
        R = 6371
        dist = 2*R*np.arcsin(np.sqrt(np.power(np.sin((phi2-phi1)/2),2) + np.cos(phi1)*np.cos(phi2)*np.power(np.sin((lam2-lam1)/2),2)))
        return dist


class MercatorCoord():


    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
    
    def __repr__(self) -> str:
        return f"<MercatorCoord lat:{self.x}, lon:{self.y}>"
    
    def __add__(self, other):
        return MercatorCoord(self.x+other.x, self.y+other.y)
    
    def __sub__(self, other):
        return MercatorCoord(self.x-other.x, self.y-other.y)
    
    def __rmul__(self, scalar: float):
        if isinstance(scalar, (int, np.integer)) or isinstance(scalar, (float, np.floating)):
            return MercatorCoord(scalar*self.x, scalar*self.y)
        else:
            raise NotImplementedError

    def __truediv__(self, scalar: float):
        if isinstance(scalar, (int, np.integer)) or isinstance(scalar, (float, np.floating)):
            return MercatorCoord(self.x/scalar, self.y/scalar)
        else:
            raise NotImplementedError
    
    
    def to_geo(self) -> GeoCoord:
        lat = self.mercator2geo_lat(self.y)
        lon = self.mercator2geo_lon(self.x)
        return GeoCoord(lat, lon)
    
    def dist(self, other) -> float:
        return self.euclidian_dist(self.x, self.y, other.x, other.y)
    
    def angle(self, other) -> float:
        return np.arctan2(self.y-other.y, self.x-other.x)


    # Inverse Mercator projection
    @staticmethod
    def mercator2geo_lat(y):
        phi = 2*np.arctan(np.exp(y)) - np.pi/2
        lat = np.rad2deg(phi)
        return lat
    @staticmethod
    def mercator2geo_lon(x):
        lam = x
        lon = np.rad2deg(lam)
        return lon
    # Euclidian distance
    @staticmethod
    def euclidian_dist(x1, y1, x2, y2):
        dist = np.sqrt(np.power(x1-x2, 2) + np.power(y1-y2, 2))
        return dist


class Tile:

    def __init__(self, x, y, zoom):
        self.x = x
        self.y = y
        self.zoom = zoom
        self.xmin = self.x
        self.xmax = self.x + 1
        self.ymin = self.y
        self.ymax = self.y + 1
        self.geo_coord_min = GeoCoord(self.tile2geo_lat(self.ymax, self.zoom), self.tile2geo_lon(self.xmin, self.zoom))
        self.geo_coord_max = GeoCoord(self.tile2geo_lat(self.ymin, self.zoom), self.tile2geo_lon(self.xmax, self.zoom))

    @classmethod
    def from_geo(self, geo_coord, zoom):
        x = self.geo2tile_x(geo_coord.lon, zoom)
        y = self.geo2tile_y(geo_coord.lat, zoom)
        return Tile(x, y, zoom)
    
    def __repr__(self):
        return f"<Tile x:{self.x}, y:{self.y}, coord_min:{self.geo_coord_min}, coord_max:{self.geo_coord_max}>"

    # Tile numbering
    @staticmethod
    def geo2tile_x(lon, zoom):
        x = int(np.floor((lon+180)/360*np.power(2,zoom)))
        return x
    @staticmethod
    def geo2tile_y(lat, zoom):
        y = int(np.floor((1-np.log(np.tan(lat*np.pi/180)+1/np.cos(lat*np.pi/180))/np.pi)*np.power(2, zoom-1)))
        return y
    # Inverse
    @staticmethod
    def tile2geo_lat(y, zoom):
        lat = np.arctan(np.sinh(np.pi - y/np.power(2, zoom)*2*np.pi))*180/np.pi
        return lat
    @staticmethod
    def tile2geo_lon(x, zoom):
        lon = x/np.power(2, zoom)*360 - 180
        return lon


if __name__ == "__main__":

    tile = Tile(4323, 5413, 13)
    print(tile)