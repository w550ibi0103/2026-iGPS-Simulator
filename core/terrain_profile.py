# -*- coding: utf-8 -*-
"""
地形剖面取樣與升取樣模組

在兩站基地台之間的連線上取樣地形高程，
支援原始精度 (20m) 與升取樣 (10m / 5m / 1m)。
升取樣使用 cubic interpolation。
"""

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import interp1d

from core.dem_loader import DEMLoader
from core.coordinate import CoordinateConverter


@dataclass
class TerrainProfile:
    """
    地形剖面資料

    Attributes
    ----------
    distances : np.ndarray
        各取樣點到起點的距離 (m)
    elevations : np.ndarray
        各取樣點的海拔高度 (m)
    coords_twd97 : list of tuple
        各取樣點的 TWD97 座標 (x, y)
    resolution_m : int
        取樣精度 (m)
    total_distance : float
        兩站之間的總距離 (m)
    station1_elevation : float
        站 A 的海拔 (m)
    station2_elevation : float
        站 B 的海拔 (m)
    """
    distances: np.ndarray
    elevations: np.ndarray
    coords_twd97: list
    resolution_m: int
    total_distance: float
    station1_elevation: float
    station2_elevation: float


class TerrainProfiler:
    """
    地形剖面提取器

    在兩站之間的連線上等距取樣地形高程，
    並可選擇性地進行升取樣 (cubic interpolation)。
    """

    NATIVE_RESOLUTION_M = 20

    def __init__(self, dem_loader: DEMLoader,
                 coord_converter: CoordinateConverter):
        self._dem = dem_loader
        self._converter = coord_converter

    def extract_profile(self, lon1: float, lat1: float,
                        lon2: float, lat2: float,
                        resolution_m: int = 20) -> TerrainProfile:
        """
        提取兩站之間的地形剖面

        Parameters
        ----------
        lon1, lat1 : float
            站 A 的 WGS84 經緯度 (度)
        lon2, lat2 : float
            站 B 的 WGS84 經緯度 (度)
        resolution_m : int
            目標取樣精度 (m)，可選 20, 10, 5, 1

        Returns
        -------
        TerrainProfile
            地形剖面資料
        """
        # 1. 轉換為 TWD97 座標
        x1, y1 = self._converter.wgs84_to_twd97(lon1, lat1)
        x2, y2 = self._converter.wgs84_to_twd97(lon2, lat2)

        # 2. 計算兩站距離
        total_distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # 3. 以原始精度 (20m) 取樣
        num_native = max(int(total_distance / self.NATIVE_RESOLUTION_M) + 1, 2)
        t_native = np.linspace(0, 1, num_native)
        x_native = x1 + t_native * (x2 - x1)
        y_native = y1 + t_native * (y2 - y1)
        distances_native = t_native * total_distance

        # 取得各點海拔
        coords_native = list(zip(x_native, y_native))
        elevations_native = self._dem.get_elevations_batch(coords_native)

        # 4. 若需要升取樣 (resolution_m < 20m)，使用 cubic interpolation
        if resolution_m < self.NATIVE_RESOLUTION_M:
            num_upsampled = max(int(total_distance / resolution_m) + 1, 2)
            distances_up = np.linspace(0, total_distance, num_upsampled)

            interp_func = interp1d(
                distances_native, elevations_native,
                kind='cubic', fill_value='extrapolate'
            )
            elevations_up = interp_func(distances_up)

            t_up = distances_up / total_distance
            x_up = x1 + t_up * (x2 - x1)
            y_up = y1 + t_up * (y2 - y1)
            coords_up = list(zip(x_up, y_up))

            distances = distances_up
            elevations = elevations_up
            coords = coords_up
        else:
            distances = distances_native
            elevations = elevations_native
            coords = coords_native

        station1_elev = elevations[0]
        station2_elev = elevations[-1]

        return TerrainProfile(
            distances=distances,
            elevations=elevations,
            coords_twd97=coords,
            resolution_m=resolution_m,
            total_distance=total_distance,
            station1_elevation=station1_elev,
            station2_elevation=station2_elev,
        )
