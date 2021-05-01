"""Script that draws an image of Southeast Asia and some surrounding parts.

Much of this could be factored out into more general utility functions and interfaces.
"""
from PIL import Image, ImageDraw
import shapefile

BORDER = 20
PIXELS_PER_DEGREE = 20
ALL_COUNTRY_RECORDS = shapefile.Reader("./data/ne_50m_admin_0_countries.shp")

""" These names match with those in ALL_COUNTRY_RECORDS. 
Change to a different set of countries and near countries to get a different map."""
SEA_COUNTRIES = ['Indonesia', 'Philippines', 'Vietnam', 'Thailand', 'Myanmar', 'Malaysia', 'Singapore', 'Cambodia',
                 'Laos', 'Brunei', 'East Timor']
NEAR_COUNTRIES = ["People's Republic of China", 'India', 'Bangladesh', 'Taiwan', 'Australia', 'Papua New Guinea', 'Bhutan']

# Routine for setting up overall bounding box, using the excuse that these are literally "global" variables.
polygons = []
for shape in ALL_COUNTRY_RECORDS.shapeRecords():
    if shape.record['NAME_EN'] in SEA_COUNTRIES:
        polygons.append(shape.shape.points)

all_points = [point for polygon in polygons for point in polygon]
MAXLAT = max([x[0] for x in all_points])
MINLAT = min([x[0] for x in all_points])
MAXLON = max([x[1] for x in all_points])
MINLON = min([x[1] for x in all_points])


def record_to_coords(record):
    points = record.shape.points
    parts = record.shape.parts
    all_coords = []
    for i in range(len(parts)):
        start = parts[i]
        end = parts[i + 1] if i + 1 < len(parts) else -1
        polygon = points[start:end]
        coords = [(BORDER + PIXELS_PER_DEGREE * (x[0] - MINLAT),
                   BORDER + PIXELS_PER_DEGREE * (MAXLON - x[1])) for x in polygon]
        all_coords.append(coords)
    return all_coords


def draw_sea_countries(img):
    for record in ALL_COUNTRY_RECORDS.shapeRecords():
        if record.record['NAME_EN'] not in SEA_COUNTRIES:
            continue
        for coords in record_to_coords(record):
            img.polygon(coords, fill="#dddddd", outline="grey")


def draw_near_countries(img):
    for record in ALL_COUNTRY_RECORDS.shapeRecords():
        if record.record['NAME_EN'] not in NEAR_COUNTRIES:
            continue
        for coords in record_to_coords(record):
            img.polygon(coords, fill="#eeeeee", outline="grey")


def main():
    size = [BORDER * 2 + int(PIXELS_PER_DEGREE * (MAXLAT - MINLAT)),
            BORDER * 2 + int(PIXELS_PER_DEGREE * (MAXLON - MINLON))]
    img = Image.new("RGB", size, "#f9f9f9")
    img_draw = ImageDraw.Draw(img)
    draw_sea_countries(img_draw)
    draw_near_countries(img_draw)
    img.show()


if __name__ == '__main__':
    main()
