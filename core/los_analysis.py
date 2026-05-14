# -*- coding: utf-8 -*-
"""
視線 (Line-of-Sight) 分析模組

判斷兩站基地台之間的直線是否被地形遮蔽。
考慮地球曲率校正後的地形高度。
"""

from dataclasses import dataclass

import numpy as np

from core.earth_curvature import EarthCurvature
from core.terrain_profile import TerrainProfile


@dataclass
class LOSResult:
    """
    LOS 分析結果

    Attributes
    ----------
    is_clear : bool
        視線是否暢通 (True = 無遮蔽)
    los_heights : np.ndarray
        視線直線在各取樣點的高度 (m)
    terrain_corrected : np.ndarray
        曲率校正後的地形高度 (m)
    obstruction_indices : list of int
        遮蔽點的索引
    max_obstruction_height : float
        最大遮蔽高度 (m)
    """
    is_clear: bool
    los_heights: np.ndarray
    terrain_corrected: np.ndarray
    obstruction_indices: list
    max_obstruction_height: float


class LOSAnalyzer:
    """
    視線分析器

    在兩站之間建立直線，判斷地形是否遮蔽視線。
    端點 (基地台位置) 不列入遮蔽判定。
    """

    def __init__(self, earth_curvature: EarthCurvature):
        self._curvature = earth_curvature

    def analyze(self, profile: TerrainProfile,
                h_ant1: float, h_ant2: float) -> LOSResult:
        """
        執行 LOS 分析

        Parameters
        ----------
        profile : TerrainProfile
            地形剖面資料
        h_ant1 : float
            站 A 天線高度 (m)
        h_ant2 : float
            站 B 天線高度 (m)

        Returns
        -------
        LOSResult
            LOS 分析結果
        """
        distances = profile.distances
        elevations = profile.elevations

        # 1. 套用地球曲率校正到地形高度
        terrain_corrected = self._curvature.apply_correction(
            distances, elevations
        )

        # 2. 計算兩端天線的絕對高度 (海拔 + 天線高)
        h_start = terrain_corrected[0] + h_ant1
        h_end = terrain_corrected[-1] + h_ant2

        # 3. 建立視線直線 (線性內插)
        n = len(distances)
        los_heights = np.linspace(h_start, h_end, n)

        # 4. 判斷中間取樣點是否被遮蔽 (排除端點)
        obstruction_indices = []
        max_obstruction = 0.0

        for i in range(1, n - 1):
            diff = terrain_corrected[i] - los_heights[i]
            if diff > 0:
                obstruction_indices.append(i)
                max_obstruction = max(max_obstruction, diff)

        is_clear = len(obstruction_indices) == 0

        return LOSResult(
            is_clear=is_clear,
            los_heights=los_heights,
            terrain_corrected=terrain_corrected,
            obstruction_indices=obstruction_indices,
            max_obstruction_height=max_obstruction,
        )
