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


def normalize(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def get_perpendicular_basis(ecef_center: List[float]) -> List[List[float]]:
    easting = normalize(np.cross([0, 0, 1], ecef_center))
    return [list(easting), list(normalize(np.cross(ecef_center, easting)))]


def euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    diff = np.array(point1) - np.array(point2)
    return np.linalg.norm(diff)


def filter_outliers(xy_points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    filtered_points = []
    for i in range(len(xy_points)):
        before_point = xy_points[i - 1]
        this_point = xy_points[i]
        after_point = xy_points[i + 1] if i < len(xy_points) - 1 else xy_points[0]
        if (euclidean_distance(this_point, before_point) < 10 * euclidean_distance(before_point, after_point)
                and euclidean_distance(this_point, after_point) < 10 * euclidean_distance(before_point, after_point)):
            filtered_points.append(this_point)
        else:
            print("Filtering a point ...")
    return filtered_points


class MapFrame:
    """Holds the state and operations for mapping shapes in curvilinear coordinates to a rectangular map frame"""
    def __init__(self, ecef_bounds: List[Tuple[float, float]]):
        if len(ecef_bounds) != 3:
            raise ValueError("MapFrame must be initialized with exactly 3 pairs of min-max bounds.")
        self.ecef_bounds = ecef_bounds
        self.ecef_center = [(bound[0] + bound[1]) / 2 for bound in ecef_bounds]
        self.basis = get_perpendicular_basis(self.ecef_center)
        corners = [(ecef_bounds[0][i], ecef_bounds[1][j], ecef_bounds[2][k])
                   for i in range(2) for j in range(2) for k in range(2)]
        self.x_width = 2 * max([np.dot(corner, self.basis[0]) for corner in corners])
        self.y_width = 2 * max([np.dot(corner, self.basis[1]) for corner in corners])

    def __str__(self):
        return f"Mapframe with center: {self.ecef_center}\nBounds:{self.ecef_bounds}\n" \
               f"x_width: {self.x_width}\ty_width: {self.y_width}\t"

    @classmethod
    def from_points(cls, lon_lat_points: List[Tuple[float, float]]):
        return cls(get_ecef_bounds(lon_lat_points))

    def lon_lat_to_xy(self, lon_lat_point: Tuple[float, float]) -> Tuple[float, float]:
        """Returns x and y points in the plane, between 0 and 1, meant to be proportions across the map frame"""
        ecef_point = lon_lat_degrees_to_ecef(lon_lat_point)
        return ((0.5 + np.dot(ecef_point, self.basis[0]) / self.x_width),
                (0.5 + np.dot(ecef_point, self.basis[1]) / self.y_width))

    def get_horizon_disk(self) -> List[Tuple[float, float]]:
        num_points = 1000
        points = [(0.5 + (np.cos(2 * i * np.pi / num_points) / self.x_width),
                   0.5 + (np.sin(2 * i * np.pi / num_points) / self.y_width)) for i in range(num_points)]
        return points

    def shape_record_to_plane_xy(self, record: shapefile.ShapeRecord) -> List[List[Tuple[float, float]]]:
        points = record.shape.points
        parts = record.shape.parts
        all_polylines = []
        for i in range(len(parts)):
            start = parts[i]
            end = parts[i + 1] if i + 1 < len(parts) else -1
            polygon = points[start:end]
            # For now, just discard points that are over the horizon, hoping that the wraparound doesn't look bad.
            polygon = [point for point in polygon if np.dot(self.ecef_center, lon_lat_degrees_to_ecef(point)) > 0]
            # Hack to remove garbage around the south pole.
            polygon = [point for point in polygon if point[1] > -85]
            polygon = filter_outliers(polygon)
            if len(polygon) < 3:
                continue
            coords = [self.lon_lat_to_xy(point) for point in polygon]
            all_polylines.append(coords)
        return all_polylines
