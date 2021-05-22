import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import shapefile

from map_frame import MapFrame

BORDER = 20
MAX_EDGE = 1000
FONT_TYPE = "Times.ttc"


def draw_countries():
    all_country_records = shapefile.Reader("./data/ne_50m_admin_0_countries.shp")
    country_names = ["Canada", "United States of America", "Mexico"]
    for record in all_country_records.shapeRecords():
        if "probe" in record.record["NAME_EN"]:
            print(record.record["NAME_EN"])
    country_shapes = [record for record in all_country_records.shapeRecords()
                      if record.record['NAME_EN'] in country_names]

    all_points = [point for country in country_shapes for point in country.shape.points]
    frame = MapFrame.from_points(all_points)

    size = [BORDER * 2 + MAX_EDGE, BORDER * 2 + MAX_EDGE]
    img = Image.new("RGB", size, "#f9f9f9")
    img_draw = ImageDraw.Draw(img)

    for record in country_shapes:
        for polyline in frame.shape_record_to_plane_xy(record):
            plot_coords = [(BORDER + MAX_EDGE * coords[0], BORDER + MAX_EDGE * (1 - coords[1])) for coords in polyline]
            img_draw.polygon(plot_coords, fill="#dddddd", outline="grey")

    img = ImageOps.expand(img, border=3)
    img.show()
    img.save("maps/canada.png")


if __name__ == '__main__':
    draw_countries()