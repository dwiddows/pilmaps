import numpy as np
import map_frame as mf


def test_lat_lon_degrees_to_ecef():
    assert np.allclose(mf.lon_lat_degrees_to_ecef([0, 0]), [1, 0, 0])
    assert np.allclose(mf.lon_lat_degrees_to_ecef([0, 90]), [0, 0, 1])
    assert np.allclose(mf.lon_lat_degrees_to_ecef([90, 0]), [0, 1, 0])


def test_get_ecef_bounds():
    assert np.allclose(mf.get_ecef_bounds([[0, 0], [45, 45]]),
                       [[0.5, 1.0], [0.0, 0.5], [0.0, 0.7071067]])


def test_get_perpendicular_basis():
    assert np.allclose(mf.get_perpendicular_basis([1, 0, 0]), [[0, 1, 0], [0, 0, 1]])


def test_euclidean_distance():
    assert np.allclose(mf.euclidean_distance((0.5, 0), (0, 0.5)), 0.7071067)
