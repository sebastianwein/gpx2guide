from engineering_notation import EngNumber
from data import * 
from img import *
from units import *


class Map:


    def __init__(self, geo_coord: GeoCoord, scale: tuple[int, int], paper_size: tuple[float, float], dpi: float) -> None:

        self.scale = scale
        paper_width, paper_height = paper_size
        delta_x = self.geo2mercator_dist(self.paper2geo_dist(paper_width), geo_coord.lat)
        delta_y = self.geo2mercator_dist(self.paper2geo_dist(paper_height), geo_coord.lat)
        mercator_coord = geo_coord.to_mercator()
        xmin = mercator_coord.x - delta_x/2
        xmax = mercator_coord.x + delta_x/2
        ymin = mercator_coord.y - delta_y/2
        ymax = mercator_coord.y + delta_y/2
        lims = (xmin, xmax, ymin, ymax)
        self.img = Img(lims, paper_size, dpi)
        # drawing scale
        scale_len = 4
        eng_number = str(EngNumber(self.paper2geo_dist(scale_len)*1000))
        if eng_number[-1].isalpha():
            scale_dist = float(eng_number[:-1])
            unit = f"{eng_number[-1]}m"
        else:
            scale_dist = float(eng_number)
            unit = "m"
        self.img.scale(scale_len, scale_dist, unit)


    def route(self, geo_data: GeoData, marker=False):
        self.img.lines(geo_data.x, geo_data.y, color="red")
        if not marker: return
        delta = np.ceil(self.paper2geo_dist(1))
        for dist in range(1, int(np.max(geo_data.dist)), int(delta)):
            geo_coord1 = geo_data.find_dist(dist)
            geo_coord2 = geo_data.find_dist(dist, interpolate=False)
            mercator_coord1 = geo_coord1.to_mercator()
            mercator_coord2 = geo_coord2.to_mercator()
            angle = mercator_coord1.angle(mercator_coord2) + np.pi/2
            self.img.mark(mercator_coord1.x, mercator_coord1.y, color="red", angle=np.rad2deg(angle))
            self.img.annotate(mercator_coord1.x, mercator_coord1.y, str(dist), color="black", angle=np.rad2deg(angle))
    
    def show(self) -> None:
        self.img.show()
    

    def paper2geo_dist(self, paper_dist):
        a, b = self.scale
        dist = b/a*paper_dist/100000
        return dist
    @staticmethod
    def haversine_delta_lon(dist, lat):
        # Haversine formula for delta lat = 0
        R = 6371
        delta_lam = np.arccos(1 - 2*np.power(np.sin(dist/(2*R)),2)/np.power(np.cos(np.deg2rad(lat)),2))
        delta_lon = np.rad2deg(delta_lam)
        return delta_lon
    @staticmethod
    def geo2mercator_dist(geo_dist, lat):
        delta_lon = Map.haversine_delta_lon(geo_dist, lat)
        mercator_dist = GeoCoord.geo2mercator_x(delta_lon)
        return mercator_dist
    

if __name__ == "__main__":
    data = GeoData.from_gpx("gpx\jakobswege.gpx")
    geo_data = data[4]
    geo_coord = geo_data.mean()
    a = 1
    b = 20000
    map = Map(geo_coord, (a, b), (14.8, 21), 300)
    map.route(geo_data, marker=True)
    map.show()
