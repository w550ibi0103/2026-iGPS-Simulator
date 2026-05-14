# -*- coding: utf-8 -*-
"""
剖面圖繪製模組

使用 matplotlib 繪製兩站基地台之間的地形剖面圖。

繪圖策略（曲面地球顯示法）：
  - 地形：顯示「原始海拔」（不含曲率校正），看起來自然平坦
  - LOS / Fresnel：向下彎曲以反映地球曲率效應
  - 遮蔽判定依然基於正確的曲率校正計算結果
  
這等價於從地球表面觀察的真實視角，比「等效平面地球法」
（地形隆起 + 直線 LOS）更直觀。
"""

import numpy as np
from matplotlib.figure import Figure

from core.terrain_profile import TerrainProfile
from core.los_analysis import LOSResult
from core.fresnel import FresnelResult


class ProfilePlotter:
    """地形剖面圖繪製器（曲面地球顯示法）"""

    COLOR_TERRAIN = '#8B7355'
    COLOR_TERRAIN_EDGE = '#5C4033'
    COLOR_LOS_CLEAR = '#2ECC71'
    COLOR_LOS_BLOCKED = '#E74C3C'
    COLOR_FRESNEL = '#3498DB'
    COLOR_OBSTRUCTION = '#E74C3C'
    COLOR_ANTENNA = '#E67E22'
    COLOR_SKY = '#D6EAF8'

    def plot(self, fig: Figure,
             profile: TerrainProfile,
             los_result: LOSResult,
             fresnel_result: FresnelResult,
             h_ant1: float, h_ant2: float):
        """
        在指定的 Figure 上繪製剖面圖

        顯示策略：
        - 地形使用原始海拔 (profile.elevations)，不含曲率校正
        - LOS 和 Fresnel 線條減去曲率校正量，呈現向下彎曲的效果
        - 視覺上等價於在地球表面觀察的真實視角
        """
        fig.clear()
        ax = fig.add_subplot(111)

        distances_km = profile.distances / 1000.0
        raw_elevations = profile.elevations

        # 計算曲率校正量 = terrain_corrected - raw_elevations
        # 用來將 LOS/Fresnel 從「等效平面地球」轉換回「曲面地球」顯示
        curvature_offset = los_result.terrain_corrected - raw_elevations

        # 將 LOS 和 Fresnel 線條減去曲率校正量（向下彎曲）
        los_visual = los_result.los_heights - curvature_offset
        fresnel_upper_visual = fresnel_result.fresnel_upper - curvature_offset
        fresnel_lower_visual = fresnel_result.fresnel_lower - curvature_offset

        # ---- 1. 天空背景 ----
        ax.set_facecolor(self.COLOR_SKY)

        # ---- 2. 地形剖面：顯示原始海拔（不含曲率隆起）----
        ax.fill_between(
            distances_km, raw_elevations,
            alpha=0.7, color=self.COLOR_TERRAIN,
            label='地形'
        )
        ax.plot(distances_km, raw_elevations,
                color=self.COLOR_TERRAIN_EDGE, linewidth=1.0)

        # ---- 3. LOS 視線（向下彎曲，反映地球曲率）----
        los_color = self.COLOR_LOS_CLEAR if los_result.is_clear \
            else self.COLOR_LOS_BLOCKED
        los_label = 'LOS (暢通)' if los_result.is_clear else 'LOS (遮蔽)'
        ax.plot(distances_km, los_visual,
                color=los_color, linewidth=2.0, label=los_label)

        # ---- 4. 第一菲涅爾區邊界（向下彎曲）----
        ax.plot(distances_km, fresnel_upper_visual,
                color=self.COLOR_FRESNEL, linewidth=1.0,
                linestyle='--', alpha=0.6, label='1st Fresnel Zone')
        ax.plot(distances_km, fresnel_lower_visual,
                color=self.COLOR_FRESNEL, linewidth=1.0,
                linestyle='--', alpha=0.6)

        # ---- 5. 標記遮蔽區域 ----
        # 在「曲面地球」視角，遮蔽 = 原始地形高於彎曲後的 LOS
        if los_result.obstruction_indices:
            for j in los_result.obstruction_indices:
                ax.vlines(distances_km[j],
                          los_visual[j],
                          raw_elevations[j],
                          color=self.COLOR_OBSTRUCTION, alpha=0.3, linewidth=1)

        # ---- 6. 標注兩站天線位置 ----
        # 端點的曲率校正量為 0，所以 raw + antenna = 正確的天線高度
        ant1_h = raw_elevations[0] + h_ant1
        ax.plot(distances_km[0], ant1_h, marker='^',
                color=self.COLOR_ANTENNA, markersize=12, zorder=5)
        ax.annotate(
            f'站A\n海拔:{raw_elevations[0]:.0f}m\n'
            f'天線高:{h_ant1:.0f}m',
            xy=(distances_km[0], ant1_h), xytext=(15, 15),
            textcoords='offset points', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.8),
            arrowprops=dict(arrowstyle='->', color='gray'),
            fontfamily='Microsoft JhengHei')

        ant2_h = raw_elevations[-1] + h_ant2
        ax.plot(distances_km[-1], ant2_h, marker='^',
                color=self.COLOR_ANTENNA, markersize=12, zorder=5)
        ax.annotate(
            f'站B\n海拔:{raw_elevations[-1]:.0f}m\n'
            f'天線高:{h_ant2:.0f}m',
            xy=(distances_km[-1], ant2_h), xytext=(-15, 15),
            textcoords='offset points', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.8),
            arrowprops=dict(arrowstyle='->', color='gray'),
            ha='right', fontfamily='Microsoft JhengHei')

        # ---- 7. 軸標籤 ----
        ax.set_xlabel('距離 (km)', fontsize=10,
                       fontfamily='Microsoft JhengHei')
        ax.set_ylabel('海拔 (m)', fontsize=10,
                       fontfamily='Microsoft JhengHei')
        ax.set_title('地形剖面圖 (含地球曲率效應)', fontsize=12,
                      fontweight='bold', fontfamily='Microsoft JhengHei')
        ax.legend(loc='upper right', fontsize=8,
                  prop={'family': 'Microsoft JhengHei'})
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
