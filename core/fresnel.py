# -*- coding: utf-8 -*-
"""
第一菲涅爾區 (1st Fresnel Zone) 淨空分析模組

計算兩站之間各取樣點的第一菲涅爾區半徑，
並判斷地形是否侵入菲涅爾區。
頻率固定為 377.5 MHz (可從 config 修改)。
"""

from dataclasses import dataclass

import numpy as np

from config import WAVELENGTH_M
from core.earth_curvature import EarthCurvature
from core.los_analysis import LOSResult
from core.terrain_profile import TerrainProfile


@dataclass
class FresnelResult:
    """
    Fresnel 淨空分析結果

    Attributes
    ----------
    clearance_ratios : np.ndarray
        各中間取樣點的淨空比
    fresnel_radii : np.ndarray
        各取樣點的第一菲涅爾區半徑 (m)
    min_clearance_ratio : float
        最小淨空比
    min_clearance_index : int
        最小淨空比所在的索引
    is_clear : bool
        菲涅爾區是否完全淨空
    fresnel_upper : np.ndarray
        視線 + 菲涅爾半徑 (上邊界)
    fresnel_lower : np.ndarray
        視線 - 菲涅爾半徑 (下邊界)
    """
    clearance_ratios: np.ndarray
    fresnel_radii: np.ndarray
    min_clearance_ratio: float
    min_clearance_index: int
    is_clear: bool
    fresnel_upper: np.ndarray
    fresnel_lower: np.ndarray


class FresnelCalculator:
    """
    第一菲涅爾區淨空計算器
    端點不套用菲涅爾模型 (依需求 #15)。
    """

    def __init__(self, wavelength: float = WAVELENGTH_M,
                 earth_curvature: EarthCurvature = None):
        self._wavelength = wavelength

    @property
    def wavelength(self) -> float:
        return self._wavelength

    def first_fresnel_radius(self, d1: float, d2: float) -> float:
        """
        計算第一菲涅爾區半徑
        公式: r1 = sqrt(λ * d1 * d2 / (d1 + d2))
        """
        d_total = d1 + d2
        if d_total <= 0:
            return 0.0
        return np.sqrt(self._wavelength * d1 * d2 / d_total)

    def analyze(self, profile: TerrainProfile,
                los_result: LOSResult) -> FresnelResult:
        distances = profile.distances
        total_dist = profile.total_distance
        n = len(distances)

        fresnel_radii = np.zeros(n)
        clearance_ratios = np.full(n, np.inf)

        for i in range(1, n - 1):
            d1 = distances[i]
            d2 = total_dist - distances[i]

            radius = self.first_fresnel_radius(d1, d2)
            fresnel_radii[i] = radius

            clearance = los_result.los_heights[i] - \
                los_result.terrain_corrected[i]

            if radius > 0:
                clearance_ratios[i] = clearance / radius
            else:
                clearance_ratios[i] = np.inf

        mid_ratios = clearance_ratios[1:-1]
        min_idx_in_mid = np.argmin(mid_ratios)
        min_clearance_ratio = mid_ratios[min_idx_in_mid]
        min_clearance_index = min_idx_in_mid + 1

        fresnel_upper = los_result.los_heights + fresnel_radii
        fresnel_lower = los_result.los_heights - fresnel_radii

        return FresnelResult(
            clearance_ratios=clearance_ratios,
            fresnel_radii=fresnel_radii,
            min_clearance_ratio=min_clearance_ratio,
            min_clearance_index=min_clearance_index,
            is_clear=(min_clearance_ratio >= 1.0),
            fresnel_upper=fresnel_upper,
            fresnel_lower=fresnel_lower,
        )
