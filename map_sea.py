"""Script that draws an image of Southeast Asia and some surrounding parts.

Much of this could be factored out into more general utility functions and interfaces.
"""
import logging
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import shapefile

BORDER = 20
PIXELS_PER_DEGREE = 40
FONT_TYPE = "Times.ttc"
ALL_COUNTRY_RECORDS = shapefile.Reader("./data/ne_50m_admin_0_countries.shp")

""" These names match with those in ALL_COUNTRY_RECORDS. 
Change to a different set of countries and near countries to get a different map."""
SEA_COUNTRIES = ['Indonesia', 'Philippines', 'Vietnam', 'Thailand', 'Myanmar', 'Malaysia', 'Singapore', 'Cambodia',
                 'Laos', 'Brunei', 'East Timor']
CORE_COUNTRY_SHAPES = [record for record in ALL_COUNTRY_RECORDS.shapeRecords()
                       if record.record['NAME_EN'] in SEA_COUNTRIES]

NAME_OFFSETS = {
    "Myanmar": (-10, -40),
    "Thailand": (0, -50),
    "Laos": (-30, -40),
    "Vietnam": (115, 30),
    "Singapore": (25, 10),
    "Brunei": (-22, -12),
    "East Timor": (40, 16),
    "Cambodia": (0, -8),
    "Indonesia": (-60, 50),
    "Philippines": (125, -10),
    "Malaysia": (-40, 20)
}

NEAR_COUNTRIES = ["People's Republic of China", 'India', 'Bangladesh',
                  'Taiwan', 'Australia', 'Papua New Guinea', 'Bhutan']
NEAR_COUNTRY_SHAPES = [record for record in ALL_COUNTRY_RECORDS.shapeRecords()
                       if record.record['NAME_EN'] in NEAR_COUNTRIES]


class FlatFrame:
    """Like map_frame.MapFrame but just uses lat lon as cartesian coordinates. Only use near the equator."""
    def __init__(self, polygons):
        all_points = [point for polygon in polygons for point in polygon]
        self.maxlon = max([x[0] for x in all_points])
        self.minlon = min([x[0] for x in all_points])
        self.maxlat = max([x[1] for x in all_points])
        self.minlat = min([x[1] for x in all_points])
        self.size = [BORDER * 2 + int(PIXELS_PER_DEGREE * (self.maxlon - self.minlon)),
                     BORDER * 2 + int(PIXELS_PER_DEGREE * (self.maxlat - self.minlat))]
        self.img = Image.new("RGB", self.size, "#f9f9f9")
        self.img_draw = ImageDraw.Draw(self.img)

        logging.debug(f"Made flat frame with \nminlat {self.minlat}\nmaxlat {self.maxlat}"
                      f"\nminlon {self.minlon}\nmaxlon {self.maxlon}\nsize {self.size}")

    def intersects(self, polygon):
        return any([self.minlon < point[0] < self.maxlon and self.minlat < point[1] < self.maxlat for point in polygon])


def get_name(record):
    try:
        return record.record.NAME
    except:
        return record.record.name


def point_to_coords(lon_lat_point, frame: FlatFrame):
    lon = lon_lat_point[0]
    if lon < -180:
        lon += 360
    return (int(BORDER + PIXELS_PER_DEGREE * (lon - frame.minlon)),
            int(BORDER + PIXELS_PER_DEGREE * (frame.maxlat - lon_lat_point[1])))


def record_to_coords(record, frame: FlatFrame):
    points = record.shape.points
    parts = record.shape.parts
    all_coords = []
    if not frame.intersects(points):
        return []
    else:
        logging.debug(f"Including intersecting shape {get_name(record)}")

    for i in range(len(parts)):
        start = parts[i]
        end = parts[i + 1] if i + 1 < len(parts) else -1
        polygon = points[start:end]
        if any([10 > point[0] > -90 for point in polygon]):
            continue
        coords = [point_to_coords(point, frame) for point in polygon]
        all_coords.append(coords)
    return all_coords


def draw_countries(frame, shape_records, fill="#dddddd", outline="grey"):
    for record in shape_records:
        for coords in record_to_coords(record, frame):
            frame.img_draw.polygon(coords, fill=fill, outline=outline)


def draw_name(frame: FlatFrame, record, name_on_line=False):
    bbox = record.shape.bbox
    size = bbox[2] - bbox[0] + bbox[3] - bbox[1]
    font_size = max(math.ceil(2 + math.pow(size, 0.3) * 10), 16)
    font = ImageFont.truetype(FONT_TYPE, font_size)
    name = get_name(record)
    w, h = font.getsize(name)
    lat_lon_spot = record.shape.points[len(record.shape.points) // 2] if name_on_line \
        else [(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2]
    center = point_to_coords(lat_lon_spot, frame)
    top_left = (center[0] - w/2, center[1] - h/2)
    if name in NAME_OFFSETS:
        top_left = np.add(top_left, NAME_OFFSETS[name])
    frame.img_draw.text(top_left, name, font=font, align="center", fill="#111111")


def get_sea_base_frame(polygons, outline="grey") -> FlatFrame:
    frame = FlatFrame(polygons)
    draw_countries(frame, CORE_COUNTRY_SHAPES, outline=outline)
    draw_countries(frame, NEAR_COUNTRY_SHAPES, fill="#eeeeee")
    return frame


def countries_and_names():
    polygons = [shape.shape.points for shape in CORE_COUNTRY_SHAPES]
    frame = get_sea_base_frame(polygons)
    for core_shape in CORE_COUNTRY_SHAPES:
        draw_name(frame, core_shape)
    img = ImageOps.expand(frame.img, border=3)
    img.show()
    img.save("maps/sea_countries.png")


def lat_lon_lines():
    """Draws lines on equator and others and adds labels, including rotation.

    Actually quite a hassle to get working, might be easier to annotate manually in Mac Preview or similar."""
    frame = get_sea_base_frame([shape.shape.points for shape in CORE_COUNTRY_SHAPES])
    dash_length = 5
    # Equator and tropic of cancer - horizontal
    for start, end in [((frame.minlon - 5, 0), (frame.maxlon + 5, 0)),
                       ((frame.minlon - 5, 23.5), (frame.maxlon + 5, 23.5))]:
        plot_start, plot_end = point_to_coords(start, frame), point_to_coords(end, frame)
        while plot_start[0] < plot_end[0]:
            frame.img_draw.line((plot_start, (plot_start[0] + dash_length, plot_start[1])), fill="#333333")
            plot_start = (plot_start[0] + 2*dash_length, plot_start[1])
    # 141st meridian - vertical
    plot_start = point_to_coords((141, frame.maxlat + 5), frame)
    plot_end = point_to_coords((141, frame.minlat - 5), frame)
    while plot_start[1] < plot_end[1]:
        frame.img_draw.line((plot_start, (plot_start[0], plot_start[1] + dash_length)), fill="#333333")
        plot_start = (plot_start[0], plot_start[1] + 2 * dash_length)

    font = ImageFont.truetype(FONT_TYPE, 24)
    frame.img_draw.text(point_to_coords((133, 1.5), frame), "Equator", font=font, fill="#111111")
    frame.img_draw.text(point_to_coords((121.8, 22.5), frame),
                        "Tropic of Cancer (23.5° North)", font=font, fill="#111111")

    tmp_txt = Image.new("RGBA", (400, 50))
    tmp_draw = ImageDraw.Draw(tmp_txt)
    tmp_draw.text((0, 0), "141° East", font=font, fill="#111111")
    tmp_window = tmp_txt.rotate(270, expand=1)
    frame.img.paste(tmp_window, point_to_coords((138, 20), frame), tmp_window)

    img = ImageOps.expand(frame.img, border=3)
    img.show()
    img.save("maps/sea_lat_lon.png")


def draw_widening_river(coords, frame):
    chunk_size = 50
    chunks = [coords[i*chunk_size:(i+1)*chunk_size+1] for i in range(len(coords) // chunk_size)]
    for i, chunk in enumerate(chunks):
        frame.img_draw.line(chunk, fill="#555", width=i)


def draw_rivers():
    land_border_shapes = [record for record in ALL_COUNTRY_RECORDS.shapeRecords()
                          if record.record['NAME_EN'] in ["Myanmar", "Vietnam", "Cambodia"]]
    polygon_with_bounds = [shape.shape.points for shape in land_border_shapes]
    polygon_with_bounds.append([[88, 30]])
    frame = get_sea_base_frame(polygon_with_bounds, outline="#cccccc")
    rivers = shapefile.Reader("data/ne_10m_rivers_lake_centerlines.shp")
    sea_rivers = ["Mekong", "Lancang",
                  "Tonlé Sap", "Tonle Sap",
                  "Salween",
                  "Irrawaddy Delta", "Ayeyarwady", "N'Mai", # Irrawaddy
                  "Chao Phraya",  "Yom", "Ping",
                  "Salween", "Nu",  # Salween
                  "Brahmaputra", "Ganges", "Yarlung", "Dihang",  # Bhamaputra Ganges
                  "Hong", "Da",  # Red river, Vietnam
                  "Jinsha", "Chang Jiang", "Yalong", "Dadu", "Min"  # Yangtze
                  ]
    for record in rivers.shapeRecords():
        if frame.intersects(record.shape.points) and get_name(record) not in sea_rivers:
            continue
        for coords in record_to_coords(record, frame):
            frame.img_draw.line(coords, fill="#444", width=2)

    lakes = shapefile.Reader("data/ne_10m_lakes.shp")
    for record in lakes.shapeRecords():
        if get_name(record) not in sea_rivers:
            continue
        for coords in record_to_coords(record, frame):
            frame.img_draw.polygon(coords, fill="#777")
            frame.img_draw.line(coords, fill="#444", width=2)

    img = ImageOps.expand(frame.img, border=3)
    img.show()
    img.save("maps/sea_rivers.png")


def main():
    logging.basicConfig(level=logging.INFO)
    draw_rivers()


if __name__ == '__main__':
    main()
