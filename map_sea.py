"""Script that draws an image of Southeast Asia and some surrounding parts.

Much of this could be factored out into more general utility functions and interfaces.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import shapefile

BORDER = 20
PIXELS_PER_DEGREE = 20
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
    "Singapore": (30, 5),
    "Brunei": (-22, -12),
    "East Timor": (40, 16),
    "Cambodia": (0, -8),
    "Indonesia": (-60, 50),
    "Philippines": (125, -10),
    "Malaysia": (-40, 20)
}

NEAR_COUNTRIES = ["People's Republic of China", 'India', 'Bangladesh',
                  'Taiwan', 'Australia', 'Papua New Guinea', 'Bhutan']
NEAR_COUNTRY_SHAPES = [record for record in ALL_COUNTRY_RECORDS.shapeRecords() if
                       record.record['NAME_EN'] in NEAR_COUNTRIES]

# Routine for setting up overall bounding box, using the excuse that these are literally "global" variables.
polygons = []
for tmp_shape in ALL_COUNTRY_RECORDS.shapeRecords():
    if tmp_shape.record['NAME_EN'] in SEA_COUNTRIES:
        polygons.append(tmp_shape.shape.points)

all_points = [point for polygon in polygons for point in polygon]
MAXLON = max([x[0] for x in all_points])
MINLON = min([x[0] for x in all_points])
MAXLAT = max([x[1] for x in all_points])
MINLAT = min([x[1] for x in all_points])


def point_to_coords(lon_lat_point):
    return (int(BORDER + PIXELS_PER_DEGREE * (lon_lat_point[0] - MINLON)),
            int(BORDER + PIXELS_PER_DEGREE * (MAXLAT - lon_lat_point[1])))


def record_to_coords(record):
    points = record.shape.points
    parts = record.shape.parts
    all_coords = []
    for i in range(len(parts)):
        start = parts[i]
        end = parts[i + 1] if i + 1 < len(parts) else -1
        polygon = points[start:end]
        coords = [point_to_coords(point) for point in polygon]
        all_coords.append(coords)
    return all_coords


def draw_countries(img_draw, shape_records, fill="#dddddd"):
    for record in shape_records:
        for coords in record_to_coords(record):
            img_draw.polygon(coords, fill=fill, outline="grey")


def draw_name(img_draw, record):
    bbox = record.shape.bbox
    size = bbox[2] - bbox[0] + bbox[3] - bbox[1]
    font_size = max(math.ceil(2 + math.pow(size, 0.3) * 10), 16)
    font = ImageFont.truetype(FONT_TYPE, font_size)
    name = record.record.NAME_EN
    w, h = font.getsize(name)
    center = point_to_coords([(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2])
    top_left = (center[0] - w/2, center[1] - h/2)
    if name in NAME_OFFSETS:
        top_left = np.add(top_left, NAME_OFFSETS[name])
    img_draw.text(top_left, name, font=font, align="center", fill="#111111")


def get_base_image():
    size = [BORDER * 2 + int(PIXELS_PER_DEGREE * (MAXLON - MINLON)),
            BORDER * 2 + int(PIXELS_PER_DEGREE * (MAXLAT - MINLAT))]
    img = Image.new("RGB", size, "#f9f9f9")
    img_draw = ImageDraw.Draw(img)

    draw_countries(img_draw, CORE_COUNTRY_SHAPES)
    draw_countries(img_draw, NEAR_COUNTRY_SHAPES, fill="#eeeeee")
    return img, img_draw


def countries_and_names():
    img, img_draw = get_base_image()
    for core_shape in CORE_COUNTRY_SHAPES:
        draw_name(img_draw, core_shape)
    img = ImageOps.expand(img, border=3)
    img.show()
    img.save("maps/sea_countries.png")


def lat_lon_lines():
    """Draws lines on equator and others and adds labels, including rotation.

    Actually quite a hassle to get working, might be easier to annotate manually in Mac Preview or similar."""
    img, img_draw = get_base_image()
    dash_length = 5
    # Equator and tropic of cancer - horizontal
    for start, end in [((MINLON - 5, 0), (MAXLON + 5, 0)),
                       ((MINLON - 5, 23.5), (MAXLON + 5, 23.5))]:
        plot_start, plot_end = point_to_coords(start), point_to_coords(end)
        while plot_start[0] < plot_end[0]:
            img_draw.line((plot_start, (plot_start[0] + dash_length, plot_start[1])), fill="#333333")
            plot_start = (plot_start[0] + 2*dash_length, plot_start[1])
    # 141st meridian - vertical
    plot_start, plot_end = point_to_coords((141, MAXLAT + 5)), point_to_coords((141, MINLAT - 5))
    while plot_start[1] < plot_end[1]:
        img_draw.line((plot_start, (plot_start[0], plot_start[1] + dash_length)), fill="#333333")
        plot_start = (plot_start[0], plot_start[1] + 2 * dash_length)

    font = ImageFont.truetype(FONT_TYPE, 24)
    img_draw.text(point_to_coords((133, 1.5)), "Equator", font=font, fill="#111111")
    img_draw.text(point_to_coords((121.8, 22.5)), "Tropic of Cancer (23.5° North)", font=font, fill="#111111")

    tmp_txt = Image.new("RGBA", (400, 50))
    tmp_draw = ImageDraw.Draw(tmp_txt)
    tmp_draw.text((0, 0), "141° East", font=font, fill="#111111")
    tmp_window = tmp_txt.rotate(270, expand=1)
    img.paste(tmp_window, point_to_coords((138, 20)), tmp_window)

    img = ImageOps.expand(img, border=3)
    img.show()
    img.save("maps/sea_lat_lon.png")


def draw_rivers():
    img, img_draw = get_base_image()
    rivers = shapefile.Reader("data/ne_10m_rivers_lake_centerlines.shp")
    sea_rivers = ["Mekong", "Salween", "awady", "Menam", "Red"]
    for record in rivers.shapeRecords():
        for coords in record_to_coords(record):
            img_draw.line(coords, fill="black")

    lakes = shapefile.Reader("data/ne_10m_lakes.shp")
    for record in lakes.shapeRecords():
        for coords in record_to_coords(record):
            img_draw.polygon(coords, fill="black")

    img = ImageOps.expand(img, border=3)
    img.show()
    img.save("maps/sea_rivers.png")


def main():
    draw_rivers()


if __name__ == '__main__':
    main()
