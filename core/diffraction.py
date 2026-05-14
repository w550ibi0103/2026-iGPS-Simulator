# -*- coding: utf-8 -*-
"""
地形繞射損耗計算模組 — Deygout 多刃法 (迭代版)

使用 ITU-R P.526 推薦的 Deygout 方法計算多障礙物繞射損耗。
本版本使用 **迭代式 stack** 取代遞迴，避免 Python 遞迴深度限制。

演算法核心：
  1. 在路徑上找出 ν 最大的主要障礙物 (dominant edge)
  2. 計算該障礙物的單刃繞射損耗
  3. 將主障礙物兩側的子路徑推入 stack 繼續處理
  4. 總損耗 = 所有子路徑損耗之和
  5. 最大遞迴深度限制為 MAX_DEPTH (預設 10)

端點不參與繞射計算 (依需求 #15)。
"""

from dataclasses import dataclass

import numpy as np

from config import WAVELENGTH_M
from core.earth_curvature import EarthCurvature
from core.terrain_profile import TerrainProfile
from core.los_analysis import LOSResult


@dataclass
class DiffractionResult:
    """
    繞射損耗計算結果

    Attributes
    ----------
    total_loss_db : float
        總繞射損耗 (dB)，≥ 0
    dominant_edge_index : int
        主要障礙物在 profile 中的索引，若無障礙物則為 -1
    dominant_edge_nu : float
        主要障礙物的 ν 值
    """
    total_loss_db: float
    dominant_edge_index: int
    dominant_edge_nu: float


class DiffractionCalculator:
    """
    Deygout 多刃繞射損耗計算器 (迭代版)

    使用 ITU-R P.526 的 Deygout 方法。
    單刃損耗近似公式:
      - ν ≤ -0.78: J(ν) = 0 dB
      - ν > -0.78:  J(ν) = 6.9 + 20·log10(sqrt((ν-0.1)² + 1) + ν - 0.1)

    使用迭代式 stack 處理，避免遞迴深度限制。
    最大處理深度: MAX_DEPTH = 10 層 (ITU 實務建議 ≤ 3，這裡設寬鬆一些)
    """

    # 最大分層深度，避免過度遞迴
    # ITU-R 實務通常建議只處理 3 個主要障礙物
    MAX_DEPTH = 10

    def __init__(self, wavelength: float = WAVELENGTH_M,
                 earth_curvature: EarthCurvature = None):
        """
        Parameters
        ----------
        wavelength : float
            電磁波波長 (m)
        earth_curvature : EarthCurvature
            地球曲率校正器
        """
        self._wavelength = wavelength

    @staticmethod
    def knife_edge_loss(nu: float) -> float:
        """
        計算單一刃峰的繞射損耗 (ITU-R P.526 近似公式)

        Parameters
        ----------
        nu : float
            Fresnel-Kirchhoff 繞射參數

        Returns
        -------
        float
            繞射損耗 (dB)，≥ 0
        """
        if nu <= -0.78:
            return 0.0
        loss = 6.9 + 20.0 * np.log10(
            np.sqrt((nu - 0.1) ** 2 + 1.0) + nu - 0.1
        )
        return max(loss, 0.0)

    def _calc_nu(self, h: float, d1: float, d2: float) -> float:
        """
        計算 Fresnel-Kirchhoff 繞射參數 ν

        Parameters
        ----------
        h : float
            障礙物頂部相對於視線的高度 (m)
            正值 = 遮蔽, 負值 = 淨空
        d1 : float
            障礙物到發射端的距離 (m)
        d2 : float
            障礙物到接收端的距離 (m)

        Returns
        -------
        float
            繞射參數 ν
        """
        if d1 <= 0 or d2 <= 0:
            return -999.0
        return h * np.sqrt(
            2.0 / self._wavelength * (1.0 / d1 + 1.0 / d2)
        )

    def _find_dominant_edge(self, distances: np.ndarray,
                            terrain_corrected: np.ndarray,
                            h_start: float, h_end: float,
                            start_idx: int, end_idx: int):
        """
        在 [start_idx+1, end_idx-1] 範圍中找出 ν 最大的障礙物

        Returns
        -------
        tuple of (int, float)
            (max_nu_idx, max_nu)，若無有效障礙物則 (-1, -999)
        """
        d_start = distances[start_idx]
        d_end = distances[end_idx]
        total_seg_dist = d_end - d_start

        if total_seg_dist <= 0:
            return -1, -999.0

        max_nu = -999.0
        max_nu_idx = -1

        for i in range(start_idx + 1, end_idx):
            d1 = distances[i] - d_start
            d2 = d_end - distances[i]
            frac = d1 / total_seg_dist

            # 視線在該點的高度 (線性內插)
            los_h = h_start + frac * (h_end - h_start)

            # 障礙物相對高度 (正值 = 遮蔽)
            h_obs = terrain_corrected[i] - los_h

            nu = self._calc_nu(h_obs, d1, d2)

            if nu > max_nu:
                max_nu = nu
                max_nu_idx = i

        return max_nu_idx, max_nu

    def _deygout_iterative(self, distances: np.ndarray,
                           terrain_corrected: np.ndarray,
                           h_start: float, h_end: float,
                           start_idx: int, end_idx: int) -> float:
        """
        Deygout 迭代式演算法 (stack-based)

        使用堆疊取代遞迴，避免 Python 遞迴深度限制。
        每個堆疊元素: (start_idx, end_idx, h_start, h_end, depth)

        Parameters
        ----------
        distances : np.ndarray
            完整的距離陣列
        terrain_corrected : np.ndarray
            曲率校正後的地形高度陣列
        h_start : float
            起點天線絕對高度 (m)
        h_end : float
            終點天線絕對高度 (m)
        start_idx : int
            子路徑起點索引
        end_idx : int
            子路徑終點索引

        Returns
        -------
        float
            該路徑的總繞射損耗 (dB)
        """
        total_loss = 0.0

        # 堆疊: (start_idx, end_idx, h_start, h_end, depth)
        stack = [(start_idx, end_idx, h_start, h_end, 0)]

        while stack:
            s_idx, e_idx, h_s, h_e, depth = stack.pop()

            # 需要至少有一個中間點
            if e_idx - s_idx < 2:
                continue

            # 超過最大深度則停止
            if depth >= self.MAX_DEPTH:
                continue

            # 找出主要障礙物
            edge_idx, edge_nu = self._find_dominant_edge(
                distances, terrain_corrected,
                h_s, h_e, s_idx, e_idx
            )

            # 若 ν ≤ -0.78，該段無明顯繞射損耗
            if edge_nu <= -0.78 or edge_idx == -1:
                continue

            # 計算主障礙物的單刃損耗
            total_loss += self.knife_edge_loss(edge_nu)

            # 將左右子路徑推入堆疊
            h_edge = terrain_corrected[edge_idx]

            # 左半段: 起點 → 主障礙物
            stack.append((s_idx, edge_idx, h_s, h_edge, depth + 1))

            # 右半段: 主障礙物 → 終點
            stack.append((edge_idx, e_idx, h_edge, h_e, depth + 1))

        return total_loss

    def calculate(self, profile: TerrainProfile,
                  los_result: LOSResult,
                  h_ant1: float, h_ant2: float) -> DiffractionResult:
        """
        計算兩站之間的總繞射損耗

        Parameters
        ----------
        profile : TerrainProfile
            地形剖面資料
        los_result : LOSResult
            LOS 分析結果
        h_ant1 : float
            站 A 天線高度 (m)
        h_ant2 : float
            站 B 天線高度 (m)

        Returns
        -------
        DiffractionResult
            繞射損耗計算結果
        """
        distances = profile.distances
        terrain_corrected = los_result.terrain_corrected
        n = len(distances)

        # 兩端天線的絕對高度
        h_start = terrain_corrected[0] + h_ant1
        h_end = terrain_corrected[-1] + h_ant2

        # 先找出主障礙物 (用於結果回報)
        dominant_idx, dominant_nu = self._find_dominant_edge(
            distances, terrain_corrected,
            h_start, h_end, 0, n - 1
        )

        # 執行迭代式 Deygout 計算
        total_loss = self._deygout_iterative(
            distances, terrain_corrected,
            h_start, h_end,
            0, n - 1
        )

        return DiffractionResult(
            total_loss_db=total_loss,
            dominant_edge_index=dominant_idx,
            dominant_edge_nu=dominant_nu,
        )
