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
    country_names = ["Indonesia", "Madagascar", "Fiji", "Micronesia", "Taiwan", "Tahiti", "New Zealand"]
    # country_names = ["New Zealand", "Antarctica", "Fiji", "Indonesia", "Chile"]
    core_country_shapes = [record for record in all_country_records.shapeRecords()
                           if any([name_part in record.record['NAME_EN'] for name_part in country_names])]

    all_points = [point for country in core_country_shapes for point in country.shape.points]
    frame = MapFrame.from_points(all_points)
    print(frame)

    (plot_width, plot_height) = (MAX_EDGE, int(MAX_EDGE * frame.y_width / frame.x_width))\
        if frame.x_width > frame.y_width else (int(MAX_EDGE * frame.x_width / frame.y_width), MAX_EDGE)

    size = [BORDER * 2 + plot_width, BORDER * 2 + plot_height]
    img = Image.new("RGB", size, color="#666666")
    img_draw = ImageDraw.Draw(img)

    horizon_coords = [(BORDER + plot_width * coords[0], BORDER + plot_height * (1 - coords[1]))
                      for coords in frame.get_horizon_disk()]
    img_draw.polygon(horizon_coords, fill="#bbbbbb", outline="grey")

    for record in all_country_records.shapeRecords():
        for polyline in frame.shape_record_to_plane_xy(record):
            plot_coords = [(BORDER + plot_width * coords[0], BORDER + plot_height * (1 - coords[1]))
                           for coords in polyline]
            img_draw.polygon(plot_coords, fill="#fdfdfd", outline="grey")

    img = ImageOps.expand(img, border=3)
    img.show()
    img.save("maps/my_local_file.png")


if __name__ == '__main__':
    draw_countries()
