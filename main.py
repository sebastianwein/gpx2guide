from data import * 
from map import *


if __name__ == "__main__":

    scale = (1, 10000)
    paper_size = (14.8, 21) #  (14.8, 21)
    dpi = 300
    margin = 1

    filename = "gpx/jakobswege.gpx"
    data = GeoData.from_gpx(filename)[:1]
    maps = list()
    for track in data:
        map = Map(track.mean(), scale, paper_size, dpi)
        paper_width, paper_height = paper_size
        dx = map.paper2mercator_dist(paper_width - 2*margin)
        dy = map.paper2mercator_dist(paper_height - 2*margin)
        segments = track.segment(dx, dy)
        for i, segment in enumerate(segments):
            mercator_coord_min = segment.min().to_mercator()
            mercator_coord_max = segment.max().to_mercator()
            segment_dx = mercator_coord_max.x - mercator_coord_min.x
            segment_dy = mercator_coord_max.y - mercator_coord_min.y
            map = Map(segment.mean(), scale, sorted(paper_size, reverse=segment_dx>segment_dy), dpi)
            map.route(segment, marker=True)
            if i>0: map.route(segments[i-1], dotted=True)
            if i<len(segments)-1: map.route(segments[i+1], dotted=True)
            map.scalebar()
            maps.append(map)
    maps[0].save("out.pdf", append_maps=maps[1:])