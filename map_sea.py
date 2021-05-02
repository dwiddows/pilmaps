"""Script that draws an image of Southeast Asia and some surrounding parts.

Much of this could be factored out into more general utility functions and interfaces.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import shapefile

BORDER = 20
PIXELS_PER_DEGREE = 20
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
MAXLAT = max([x[0] for x in all_points])
MINLAT = min([x[0] for x in all_points])
MAXLON = max([x[1] for x in all_points])
MINLON = min([x[1] for x in all_points])


def point_to_coords(lat_lon_point):
    return (BORDER + PIXELS_PER_DEGREE * (lat_lon_point[0] - MINLAT),
            BORDER + PIXELS_PER_DEGREE * (MAXLON - lat_lon_point[1]))


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
    font_type = "Times.ttc"
    bbox = record.shape.bbox
    size = bbox[2] - bbox[0] + bbox[3] - bbox[1]
    font_size = max(math.ceil(2 + math.pow(size, 0.3) * 10), 16)
    font = ImageFont.truetype(font_type, font_size)
    name = record.record.NAME_EN
    w, h = font.getsize(name)
    center = point_to_coords([(bbox[0] + bbox[2])/2, (bbox[1] + bbox[3])/2])
    top_left = (center[0] - w/2, center[1] - h/2)
    if name in NAME_OFFSETS:
        top_left = np.add(top_left, NAME_OFFSETS[name])
    img_draw.text(top_left, name, font=font, align="center", fill="#111111")


def get_base_image():
    size = [BORDER * 2 + int(PIXELS_PER_DEGREE * (MAXLAT - MINLAT)),
            BORDER * 2 + int(PIXELS_PER_DEGREE * (MAXLON - MINLON))]
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
    img.save("sea_countries.png")


def main():
    countries_and_names()


if __name__ == '__main__':
    main()
