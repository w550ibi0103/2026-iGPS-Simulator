# -*- coding: utf-8 -*-
"""
地球曲率校正模組

提供地球曲率對地形高程的校正計算。
使用等效地球半徑 (k=4/3 標準大氣) 來近似大氣折射效應。
所有 LOS、Fresnel、Diffraction 計算都使用此模組的統一校正。
"""

import numpy as np

from config import EFFECTIVE_EARTH_RADIUS_M


class EarthCurvature:
    """
    地球曲率校正計算器

    使用公式: h_curve = d1 * d2 / (2 * R_eff)
    其中 d1, d2 分別為取樣點到發射端和接收端的距離。
    """

    def __init__(self, effective_radius: float = EFFECTIVE_EARTH_RADIUS_M):
        """
        Parameters
        ----------
        effective_radius : float
            等效地球半徑 (m)，預設為 R_earth * k = 6371000 * 4/3
        """
        self._effective_radius = effective_radius

    @property
    def effective_radius(self) -> float:
        """取得等效地球半徑"""
        return self._effective_radius

    def correction(self, d1: float, d2: float) -> float:
        """
        計算單一取樣點的地球曲率校正值

        Parameters
        ----------
        d1 : float
            取樣點到發射端的距離 (m)
        d2 : float
            取樣點到接收端的距離 (m)

        Returns
        -------
        float
            曲率校正值 (m)，需加到地形高度上
        """
        return (d1 * d2) / (2.0 * self._effective_radius)

    def apply_correction(self, distances: np.ndarray,
                         elevations: np.ndarray) -> np.ndarray:
        """
        對整條地形剖面套用地球曲率校正

        Parameters
        ----------
        distances : np.ndarray
            各取樣點到起點的距離 (m)
        elevations : np.ndarray
            各取樣點的原始海拔 (m)

        Returns
        -------
        np.ndarray
            曲率校正後的海拔陣列 (m)
        """
        total_distance = distances[-1]
        d1 = distances
        d2 = total_distance - distances
        corrections = (d1 * d2) / (2.0 * self._effective_radius)
        return elevations + corrections
