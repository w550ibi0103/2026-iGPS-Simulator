# -*- coding: utf-8 -*-
"""
側向地形掃描模組

以兩站連線為中心，向左右每隔取樣精度平移取樣，
比對地形高度與直線 LOS 高度，找出走廊範圍內是否有地形穿越 LOS 平面
(例如連線本身沒被擋，但兩側山壁貼得很近)。
"""

from dataclasses import dataclass

import numpy as np

from core.earth_curvature import EarthCurvature
from core.terrain_profile import TerrainProfiler


@dataclass
class LateralScanResult:
    """
    側向地形掃描結果

    Attributes
    ----------
    distances : np.ndarray
        沿線距離 (m)，與中心線剖面相同
    offsets : np.ndarray
        側向偏移量 (m)，正值為左側、負值為右側、0 為中心線本身
    terrain_corrected : np.ndarray
        二維地形高度網格 (含曲率校正)，shape = (len(offsets), len(distances))
    intrusion_mask : np.ndarray
        布林遮罩，shape 同上，True 代表該位置地形高度超過直線 LOS 高度
    """
    distances: np.ndarray
    offsets: np.ndarray
    terrain_corrected: np.ndarray
    intrusion_mask: np.ndarray


class LateralScanAnalyzer:
    """
    側向地形掃描分析器

    僅比對地形高度與直線 LOS 高度 (不套用 Fresnel 淨空準則)，
    不對側向掃描線本身進行完整 LOS/Fresnel 分析。
    """

    def __init__(self, earth_curvature: EarthCurvature):
        self._curvature = earth_curvature

    def scan(self, terrain_profiler: TerrainProfiler,
             lon1: float, lat1: float, lon2: float, lat2: float,
             resolution_m: int, scan_width_m: float,
             los_heights: np.ndarray) -> LateralScanResult:
        """
        執行側向地形掃描

        Parameters
        ----------
        terrain_profiler : TerrainProfiler
            地形剖面提取器
        lon1, lat1, lon2, lat2 : float
            兩站的 WGS84 經緯度 (度)
        resolution_m : int
            沿線取樣精度 (m)，同時作為側向掃描的取樣間距
        scan_width_m : float
            側向掃描半寬 (m)，掃描範圍為 [-scan_width_m, +scan_width_m]
        los_heights : np.ndarray
            中心線直線 LOS 高度 (m)，作為比對基準，僅與沿線距離相關

        Returns
        -------
        LateralScanResult
            側向地形掃描結果
        """
        offsets = np.arange(-scan_width_m, scan_width_m + resolution_m / 2,
                             resolution_m)

        distances = None
        elevations_rows = []
        for offset in offsets:
            profile = terrain_profiler.extract_profile(
                lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2,
                resolution_m=resolution_m, lateral_offset_m=float(offset))
            if distances is None:
                distances = profile.distances
            elevations_rows.append(profile.elevations)

        terrain_corrected = np.array([
            self._curvature.apply_correction(distances, row)
            for row in elevations_rows
        ])

        intrusion_mask = terrain_corrected > los_heights[np.newaxis, :]

        return LateralScanResult(
            distances=distances,
            offsets=offsets,
            terrain_corrected=terrain_corrected,
            intrusion_mask=intrusion_mask,
        )
