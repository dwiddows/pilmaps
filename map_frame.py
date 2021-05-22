import numpy as np
from typing import List, Tuple

import shapefile

DEGREES_TO_RADIANS = np.pi / 180


def lon_lat_degrees_to_ecef(lon_lat_degrees: Tuple[float, float]) -> Tuple[float, float, float]:
    """Maps latitude and longitude to Earth-Centered, Earth-Fixed coordinates. Earth assumed to be a unit sphere."""
    lon_rad, lat_rad = [DEGREES_TO_RADIANS * coord for coord in lon_lat_degrees]
    return np.cos(lat_rad) * np.cos(lon_rad), np.cos(lat_rad) * np.sin(lon_rad), np.sin(lat_rad)


def get_ecef_bounds(lon_lat_list: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Returns the [[min_x, max_x], [min_y, max_y], [min_z, max_z]]"""
    ecef_points = [lon_lat_degrees_to_ecef(point) for point in lon_lat_list]
    return [(min([point[i] for point in ecef_points]), max([point[i] for point in ecef_points])) for i in range(3)]


def get_perpendicular_basis(ecef_center: List[float]) -> List[List[float]]:
    easting = np.cross([0, 0, 1], ecef_center)
    return [list(easting), list(np.cross(ecef_center, easting))]


class MapFrame:
    """Holds the state and operations for mapping shapes in curvilinear coordinates to a rectangular map frame"""
    def __init__(self, ecef_bounds: List[Tuple[float, float]]):
        self.ecef_bounds = ecef_bounds
        self.ecef_center = [(bound[0] + bound[1]) / 2 for bound in ecef_bounds]
        self.basis = get_perpendicular_basis(self.ecef_center)
        # TODO: Make scale rectangular not just assuming a square.
        max_cos = np.dot(self.ecef_center, [b[1] for b in ecef_bounds])
        self.plane_scale = 2 * np.sqrt(2) / np.sqrt(1 - max_cos * max_cos)

    @classmethod
    def from_points(cls, lon_lat_points: List[Tuple[float, float]]):
        return cls(get_ecef_bounds(lon_lat_points))

    def lon_lat_to_xy(self, lon_lat_point: Tuple[float, float]) -> Tuple[float, float]:
        """Returns x and y points in the plane, between 0 and 1, meant to be proportions across the map frame"""
        ecef_point = lon_lat_degrees_to_ecef(lon_lat_point)
        return ((1 + self.plane_scale * np.dot(ecef_point, self.basis[0])) / 2,
                (1 + self.plane_scale * np.dot(ecef_point, self.basis[1])) / 2)

    def shape_record_to_plane_xy(self, record: shapefile.ShapeRecord) -> List[List[Tuple[float, float]]]:
        points = record.shape.points
        parts = record.shape.parts
        all_coords = []
        for i in range(len(parts)):
            start = parts[i]
            end = parts[i + 1] if i + 1 < len(parts) else -1
            polygon = points[start:end]
            coords = [self.lon_lat_to_xy(point) for point in polygon]
            all_coords.append(coords)
        return all_coords
